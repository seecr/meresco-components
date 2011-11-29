## begin license ##
# 
# "Meresco Oai" are components to build Oai repositories, based on
# "Meresco Core" and "Meresco Components". 
# 
# Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# 
# This file is part of "Meresco Oai"
# 
# "Meresco Oai" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Meresco Oai" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Meresco Oai"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from __future__ import with_statement
from contextlib import contextmanager
from random import randint
from threading import Event, Thread
from time import sleep
from socket import socket, error as SocketError
from lxml.etree import tostring
from StringIO import StringIO
from os.path import join

from cq2utils import CQ2TestCase, CallTrace
from weightless.core import be
from meresco.core import Observable
from meresco.components.http.utils import CRLF
from meresco.components import PeriodicDownload

DROP_CONNECTION = object()

@contextmanager
def server(responses, bufsize=4096):
    port = randint(10000,60000)
    start = Event()
    messages = []
    def serverThread():
        s = socket()
        s.bind(('127.0.0.1', port))
        s.listen(0)
        start.set()
        for response in responses:
            connection, address = s.accept()
            msg = connection.recv(bufsize)
            messages.append(msg)
            if not response is DROP_CONNECTION:
                connection.send(response)
                connection.close()
    thread = Thread(None, serverThread)
    thread.start()
    start.wait()
    yield port, messages
    thread.join()


class PeriodicDownloadTest(CQ2TestCase):
    def testOne(self):
        reactor = CallTrace("reactor")
        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            harvester, observer, reactor = self.getHarvester("localhost", port)
            self.assertEquals('addTimer', reactor.calledMethods[0].name)
            self.assertEquals(1, reactor.calledMethods[0].args[0])
            callback = reactor.calledMethods[0].args[1]
            callback() # connect
            self.assertEquals('addWriter', reactor.calledMethods[1].name)
            callback = reactor.calledMethods[1].args[1]
            callback() # HTTP GET
            sleep(0.01)
            self.assertEquals("GET", msgs[0][:3])
            self.assertEquals('removeWriter', reactor.calledMethods[2].name)
            self.assertEquals('addReader', reactor.calledMethods[3].name)
            self.assertEquals(0, reactor.calledMethods[3].kwargs['prio'])
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv
            callback() # sok.recv
            callback() # yield after self.do.add(...
            self.assertEquals("", harvester._err.getvalue())
            self.assertEquals('buildRequest', observer.calledMethods[0].name)
            self.assertEquals('handle', observer.calledMethods[1].name)
            self.assertEquals(0, len(observer.calledMethods[1].args))
            self.assertEquals(['data'], observer.calledMethods[1].kwargs.keys())
            self.assertEqualsWS(ONE_RECORD, observer.calledMethods[1].kwargs['data'])

    def testNoConnectionPossible(self):
        harvester, observer, reactor = self.getHarvester("some.nl", 'no-port')
        callback = reactor.calledMethods[0].args[1]
        try:
            callback() # connect
            self.fail()
        except TypeError, e:
            self.assertEquals("an integer is required", str(e))

    def testErrorResponse(self):
        reactor = CallTrace("reactor")
        with server(['HTTP/1.0 400 Error\r\n\r\nIllegal Request']) as (port, msgs):
            harvester, observer, reactor = self.getHarvester("localhost", port)
            callback = reactor.calledMethods[0].args[1]
            callback() # connect
            callback = reactor.calledMethods[1].args[1]
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv

            callback() # yield After Error 

            self.assertEquals("localhost:%d: Unexpected response: HTTP/1.0 400 Error\n" % port, harvester._err.getvalue())
            self.assertEquals(['buildRequest'], [m.name for m in observer.calledMethods])

    def testInvalidPortConnectionRefused(self):
        harvester, observer, reactor = self.getHarvester("localhost", 88)
        callback = reactor.calledMethods[0].args[1]
        callback() # connect
        self.assertEquals("addWriter", reactor.calledMethods[1].name)
        callback() # connect
        self.assertEquals("removeWriter", reactor.calledMethods[2].name)
        self.assertEquals("addTimer", reactor.calledMethods[3].name)
        self.assertEquals("localhost:88: Connection refused.\n", harvester._err.getvalue())

    def testInvalidHost(self):
        strangeHost = "UEYR^$*FD(#>NDJ.khfd9.(*njnd.nl"
        harvester, observer, reactor = self.getHarvester(strangeHost, 88)
        callback = reactor.calledMethods[0].args[1]
        callback() # connect
        self.assertEquals('addTimer', reactor.calledMethods[-1].name)
        nameOrServiceNotKnown = strangeHost + ":88: -2: Name or service not known\n" ==  harvester._err.getvalue()
        noAddressAssociatedWithHost = strangeHost + ":88: -5: No address associated with hostname\n" == harvester._err.getvalue()
        self.assertTrue(nameOrServiceNotKnown or noAddressAssociatedWithHost, harvester._err.getvalue())

    def testInvalidHostConnectionRefused(self):
        harvester, observer, reactor = self.getHarvester("127.0.0.255", 9876)
        callback = reactor.calledMethods[0].args[1]
        callback()
        self.assertEquals("addWriter", reactor.calledMethods[1].name)
        callback()
        self.assertEquals("127.0.0.255:9876: Connection refused.\n", harvester._err.getvalue())
        self.assertEquals("removeWriter", reactor.calledMethods[2].name)
        self.assertEquals("addTimer", reactor.calledMethods[3].name)

    def testSuccess(self):
        with server([RESPONSE_TWO_RECORDS]) as (port, msgs):
            harvester, observer, reactor = self.getHarvester("localhost", port)
            self.assertEquals(1, harvester._period)
            callback = self.doConnect()
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv
            callback() # recv = ''
            callback() # yield after addReader()
            callback() # yield after self.do.add(...
            self.assertEquals("", harvester._err.getvalue())
            self.assertEquals('buildRequest', observer.calledMethods[0].name)
            self.assertEquals('handle', observer.calledMethods[1].name)
            self.assertEqualsWS(TWO_RECORDS, observer.calledMethods[1].kwargs['data'])
            self.assertEquals('removeReader', reactor.calledMethods[-2].name)
            self.assertEquals('addTimer', reactor.calledMethods[-1].name)

    def testSuccessHttp1dot1Server(self):
        with server([STATUSLINE_ALTERNATIVE + ONE_RECORD]) as (port, msgs):
            harvester, observer, reactor = self.getHarvester("localhost", port)
            callback = self.doConnect()
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv
            callback() # recv = ''
            callback() # yield after addReader()
            callback() # yield after self.do.add(...
            self.assertEquals("", harvester._err.getvalue())
            self.assertEquals('buildRequest', observer.calledMethods[0].name)
            self.assertEqualsWS(ONE_RECORD, observer.calledMethods[1].kwargs['data'])

    def testPeriod(self):
        with server([RESPONSE_TWO_RECORDS, 'HTTP/1.0 400 Error\r\n\r\nIllegal Request']) as (port, msgs):
            harvester, observer, reactor = self.getHarvester("localhost", port, period=2)
            callback = self.doConnect()
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv
            callback() # recv = ''
            callback() # yield after addReader()
            callback() # yield after self.do.add(...
            self.assertEquals('addTimer', reactor.calledMethods[-1].name)
            self.assertEquals(2, reactor.calledMethods[-1].args[0])
            
            callback = self.doConnect()
            callback() # HTTP GET
            sleep(0.01)
            callback() # sok.recv
            callback() # recv = ''
            self.assertEquals('addTimer', reactor.calledMethods[-1].name)
            self.assertEquals(2, reactor.calledMethods[-1].args[0])

    def testRecoveringAfterDroppedConnection(self):
        with server([DROP_CONNECTION, RESPONSE_ONE_RECORD]) as (port, msgs):
            harvester, observer, reactor = self.getHarvester("localhost", port)
            callback = self.doConnect()
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv = ''
            self.assertEquals("localhost:%s: Receive error: 11: Resource temporarily unavailable\n" % port, harvester._err.getvalue()) 
            callback()
            callback() # HTTP GET
            sleep(0.01)
            self.assertEquals("GET /path?argument=value HTTP/1.0\r\n\r\n", msgs[0])
            callback() # sok.recv
            callback() # soc.recv == ''
            callback() # removeReader() after self.do.add(...
            self.assertEquals(['buildRequest', 'buildRequest', 'handle'], [m.name for m in observer.calledMethods])

    def getHarvester(self, host, port, period=1):
        self._reactor = CallTrace("reactor")
        self._harvester = PeriodicDownload(self._reactor, host, port, period=period, prio=0, err=StringIO())
        self._observer = CallTrace("observer")
        self._observer.returnValues["buildRequest"] = "GET /path?argument=value HTTP/1.0\r\n\r\n"
        self._harvester.addObserver(self._observer)
        self._harvester.observer_init()
        self.assertEquals(1, self._reactor.calledMethods[0].args[0])
        return self._harvester, self._observer, self._reactor

    def doConnect(self):
        callback = self._reactor.calledMethods[0].args[1]
        callback() # connect
        callback = self._reactor.calledMethods[1].args[1]
        return callback

HTTP_SEPARATOR = 2 * CRLF
STATUSLINE = """HTTP/1.0 200 OK """ + HTTP_SEPARATOR
STATUSLINE_ALTERNATIVE = """HTTP/1.1 200 ok """ + HTTP_SEPARATOR

EMBEDDED_RECORD = '<record>ignored</record>'
BODY = """<aap:noot xmlns:aap="mies">%s</aap:noot>"""
ONE_RECORD = BODY % (EMBEDDED_RECORD) 
TWO_RECORDS = BODY % (EMBEDDED_RECORD * 2) 
RESPONSE_ONE_RECORD = STATUSLINE + ONE_RECORD 
RESPONSE_TWO_RECORDS = STATUSLINE + TWO_RECORDS 

