## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# 
# This file is part of "Meresco Components"
# 
# "Meresco Components" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Meresco Components" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Meresco Components"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from __future__ import with_statement
from contextlib import contextmanager
from random import randint
from threading import Event, Thread
from time import sleep
from socket import socket, error as SocketError
from meresco.components import lxmltostring
from StringIO import StringIO
from os.path import join
from urllib2 import urlopen
from time import time

from seecr.test import SeecrTestCase, CallTrace
from seecr.test.io import stderr_replaced
from seecr.test.utils import ignoreLineNumbers

from weightless.core import be, compose
from weightless.io import Reactor, Suspend

from meresco.core import Observable

from meresco.components.http.utils import CRLF
from meresco.components import PeriodicDownload

def _dunderFile(): pass
fileDict = {
    '__file__': _dunderFile.func_code.co_filename,
    'periodicdownload.py': PeriodicDownload.__init__.func_code.co_filename,
}

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
            try:
                connection, address = s.accept()
                msg = connection.recv(bufsize)
                messages.append(msg)
                if not response is DROP_CONNECTION:
                    connection.send(response)
                    connection.close()
            except:
                pass
    thread = Thread(None, serverThread)
    thread.start()
    start.wait()
    yield port, messages
    thread.join()


class PeriodicDownloadTest(SeecrTestCase):
    def testOne(self):
        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            downloader, observer, reactor = self.getDownloader("localhost", port)
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
            self.assertEquals("", downloader._err.getvalue())
            self.assertEquals('buildRequest', observer.calledMethods[0].name)
            callback() # addProcess
            self.assertEquals('handle', observer.calledMethods[1].name)
            self.assertEquals(0, len(observer.calledMethods[1].args))
            self.assertEquals(['data'], observer.calledMethods[1].kwargs.keys())
            self.assertEqualsWS(ONE_RECORD, observer.calledMethods[1].kwargs['data'])
            callback()
            self.assertReactorState(reactor)

    def testNoConnectionPossibleWithNonIntegerPort(self):
        downloader, observer, reactor = self.getDownloader("some.nl", 'no-port')
        callback = reactor.calledMethods[0].args[1]
        callback() # connect
        self.assertEquals("some.nl:no-port: an integer is required\n", downloader._err.getvalue())
        self.assertReactorState(reactor)

    def testNoConnectionPossible(self):
        downloader, observer, reactor = self.getDownloader("localhost", 8899)
        callback = reactor.calledMethods[0].args[1]
        callback() # connect
        reactor.exceptions['removeWriter'] = IOError("error in sockopt") ## Simulate IOError as raised from sok.getsockopt
        callback = reactor.calledMethods[1].args[1]
        callback() # HTTP GET
        self.assertEquals("localhost:8899: error in sockopt\n", downloader._err.getvalue())
        del reactor.exceptions['removeWriter']
        self.assertEquals('addTimer', reactor.calledMethods[-1].name)
        self.assertEquals(1 + 5*60, reactor.calledMethods[-1].args[0])

        self.assertReactorState(reactor)

        callback = reactor.calledMethods[-1].args[1]
        callback() # connect
        self.assertEquals("addWriter", reactor.calledMethods[-1].name)
        self.assertEquals("localhost:8899: error in sockopt\n", downloader._err.getvalue()) # remains 1 error
 
    def testVerboseDeprecationWarning(self):
        with stderr_replaced() as s:
            PeriodicDownload(reactor='x', host='x', port='x')
            result = s.getvalue()
            self.assertEquals('', result)

        with stderr_replaced() as s:
            PeriodicDownload(reactor='x', host='x', port='x', verbose=True)
            result = s.getvalue()
            self.assertTrue('DeprecationWarning: Verbose flag is deprecated' in result, result)

    def testErrorResponse(self):
        with server(['HTTP/1.0 400 Error\r\nContent-Type: text/plain\r\n\r\nIllegal Request']) as (port, msgs):
            downloader, observer, reactor = self.getDownloader("localhost", port)
            callback = reactor.calledMethods[0].args[1]
            callback() # connect
            callback = reactor.calledMethods[1].args[1]
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv

            callback() # yield After Error 

            self.assertEquals("localhost:%d: Unexpected response: HTTP/1.0 400 Error\r\nContent-Type: text/plain\r\n\r\nIllegal Request\nFor request: GET /path?argument=value HTTP/1.0\r\n\r\n" % port, downloader._err.getvalue())
            self.assertEquals(['buildRequest'], [m.name for m in observer.calledMethods])
            self.assertReactorState(reactor)

    def testInvalidPortConnectionRefused(self):
        downloader, observer, reactor = self.getDownloader("localhost", 88)
        callback = reactor.calledMethods[0].args[1]
        callback() # startProcess
        self.assertEquals("addWriter", reactor.calledMethods[1].name)
        callback = reactor.calledMethods[1].args[1]
        callback() # _processOne.next
        self.assertEquals("removeWriter", reactor.calledMethods[2].name)
        self.assertEquals("addTimer", reactor.calledMethods[3].name)
        self.assertEquals("localhost:88: Connection refused.\n", downloader._err.getvalue())
        self.assertReactorState(reactor)

    def testInvalidHost(self):
        strangeHost = "UEYR^$*FD(#>NDJ.khfd9.(*njnd.nl"
        downloader, observer, reactor = self.getDownloader(strangeHost, 88)
        callback = reactor.calledMethods[0].args[1]
        callback() # connect
        self.assertEquals('addTimer', reactor.calledMethods[-1].name)
        nameOrServiceNotKnown = strangeHost + ":88: -2: Name or service not known\n" ==  downloader._err.getvalue()
        noAddressAssociatedWithHost = strangeHost + ":88: -5: No address associated with hostname\n" == downloader._err.getvalue()
        self.assertTrue(nameOrServiceNotKnown or noAddressAssociatedWithHost, downloader._err.getvalue())
        self.assertReactorState(reactor)

    def testInvalidHostConnectionRefused(self):
        downloader, observer, reactor = self.getDownloader("127.0.0.255", 9876)
        callback = reactor.calledMethods[0].args[1]
        callback() # startProcess
        self.assertEquals("addWriter", reactor.calledMethods[1].name)
        callback = reactor.calledMethods[1].args[1]
        callback() # _processOne.next
        self.assertEquals("127.0.0.255:9876: Connection refused.\n", downloader._err.getvalue())
        self.assertEquals("removeWriter", reactor.calledMethods[2].name)
        self.assertEquals("addTimer", reactor.calledMethods[3].name)
        self.assertReactorState(reactor)

    def testSuccess(self):
        with server([RESPONSE_TWO_RECORDS]) as (port, msgs):
            downloader, observer, reactor = self.getDownloader("localhost", port)
            self.assertEquals(1, downloader._period)
            callback = self.doConnect() # _processOne.next
            callback() # _processOne.next -> HTTP GET
            self.assertEquals('buildRequest', observer.calledMethods[0].name)
            sleep(0.01)
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''
            callback() # addProcess
            self.assertEquals("", downloader._err.getvalue())
            self.assertEquals('handle', observer.calledMethods[1].name)
            self.assertEqualsWS(TWO_RECORDS, observer.calledMethods[1].kwargs['data'])
            self.assertEquals('addProcess', reactor.calledMethods[-1].name)
            callback() # _processOne.next
            self.assertEquals('removeProcess', reactor.calledMethods[-2].name)
            self.assertEquals('addTimer', reactor.calledMethods[-1].name)
            self.assertReactorState(reactor)

    def testSuccessWithSuspend(self):
        suspendObject = Suspend()
        with server([RESPONSE_TWO_RECORDS]) as (port, msgs):
            downloader, observer, reactor = self.getDownloader("localhost", port, handleGenerator=(x for x in ['X', suspendObject]))
            self.assertEquals(1, downloader._period)
            callback = self.doConnect() # _processOne.next
            callback() # _processOne.next -> HTTP GET
            self.assertEquals('buildRequest', observer.calledMethods[0].name)
            sleep(0.01)
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''
            callback() # addProcess
            self.assertEquals("", downloader._err.getvalue())
            self.assertEquals('handle', observer.calledMethods[1].name)
            self.assertEqualsWS(TWO_RECORDS, observer.calledMethods[1].kwargs['data'])
            self.assertEquals('addProcess', reactor.calledMethods[-1].name)
            callback = reactor.calledMethods[-1].args[0]
            callback() 
            self.assertEquals('suspend', reactor.calledMethods[-1].name)
            suspendObject.resume("resume response")
            self.assertEquals('resumeProcess', reactor.calledMethods[-1].name)
            callback()
            self.assertEquals('removeProcess', reactor.calledMethods[-2].name)
            self.assertEquals('addTimer', reactor.calledMethods[-1].name)
            self.assertReactorState(reactor)

    def testRaiseInHandle(self):
        def handleGenerator():
            yield 'first'
            raise Exception('xcptn')
            yield

        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            downloader, observer, reactor = self.getDownloader("localhost", port, handleGenerator=handleGenerator())
            callback = self.doConnect() # _processOne.next
            callback() # _processOne.next -> HTTP GET
            self.assertEquals('buildRequest', observer.calledMethods[0].name)
            sleep(0.01)
            self.assertEquals(['GET /path?argument=value HTTP/1.0\r\n\r\n'], msgs) # message received, getting response
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''; then addProcess
            callback() # first self.all.handle(data=body) -> 1st response

            result = downloader._err.getvalue()
            self.assertEquals('', result)

            callback() # 2nd response / raise Exception(...)
            result = downloader._err.getvalue()
            self.assertTrue('Traceback' in result, result)
            expected =  ignoreLineNumbers("""localhost:%(port)s: Traceback (most recent call last):
  File "%%(periodicdownload.py)s", line 104, in processOne
    for _response  in g:
  File "%%(__file__)s", line 243, in handleGenerator
    raise Exception('xcptn')
Exception: xcptn
Error while processing response: HTTP/1.0 200 OK \r\n\r\n<aap:noot xmlns:aap="mies"><record>ignored</record></aap:noot>
For request: GET /path?argument=value HTTP/1.0\r\n\r\n""" % {'port': port} % fileDict)
            self.assertEquals(expected, ignoreLineNumbers(result))

            self.assertEquals('removeProcess', reactor.calledMethods[-2].name)
            self.assertEquals('addTimer', reactor.calledMethods[-1].name)
            self.assertReactorState(reactor)

    def testAssertionErrorReraised(self):
        with server([RESPONSE_TWO_RECORDS]) as (port, msgs):
            downloader, observer, reactor = self.getDownloader("localhost", port)
            observer.methods['handle'] = lambda *args, **kwargs: None  # will cause AssertionError in Observable

            self.assertEquals(1, downloader._period)
            callback = self.doConnect() # _processOne.next
            callback() # _processOne.next -> HTTP GET
            self.assertEquals('buildRequest', observer.calledMethods[0].name)
            sleep(0.01)
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''
            try:
                callback() # addProcess
                self.assertEquals('', self._downloader._err.getvalue())
                self.fail('should not get here')
            except AssertionError, e:
                self.assertEquals('<bound method handle of <CallTrace: observer>> should have resulted in a generator.', str(e))
          
    def testSuccessHttp1dot1Server(self):
        with server([STATUSLINE_ALTERNATIVE + ONE_RECORD]) as (port, msgs):
            downloader, observer, reactor = self.getDownloader("localhost", port)
            callback = self.doConnect()
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv
            callback() # recv = ''
            callback() # addProcess
            self.assertEquals("", downloader._err.getvalue())
            self.assertEquals('buildRequest', observer.calledMethods[0].name)
            self.assertEqualsWS(ONE_RECORD, observer.calledMethods[1].kwargs['data'])
            callback()
            self.assertReactorState(reactor)

    def testPeriod(self):
        with server([RESPONSE_TWO_RECORDS, 'HTTP/1.0 400 Error\r\n\r\nIllegal Request']) as (port, msgs):
            downloader, observer, reactor = self.getDownloader("localhost", port, period=2)
            callback = self.doConnect()
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[-1].args[1]
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''
            callback() # _processOne.next
            self.assertEquals('addProcess', reactor.calledMethods[-1].name)
            callback = reactor.calledMethods[-1].args[0]
            callback() # _processOne.next
            self.assertEquals('addTimer', reactor.calledMethods[-1].name)
            self.assertEquals(2, reactor.calledMethods[-1].args[0])
            
            callback = reactor.calledMethods[-1].args[1]
            callback() # startProcess
            callback = reactor.calledMethods[-1].args[1]
            callback() # _processOne.next -> HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[-1].args[1]
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''
            # error status
            self.assertEquals('addTimer', reactor.calledMethods[-1].name)
            self.assertEquals(2, reactor.calledMethods[-1].args[0])
            self.assertReactorState(reactor)

    def testRecoveringAfterDroppedConnection(self):
        with server([DROP_CONNECTION, RESPONSE_ONE_RECORD]) as (port, msgs):
            downloader, observer, reactor = self.getDownloader("localhost", port)
            callback = self.doConnect()
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[-1].args[1]
            callback() # _processOne.next -> sok.recv
            self.assertEquals("localhost:%d: Receive error: 11: Resource temporarily unavailable\nFor request: GET /path?argument=value HTTP/1.0\r\n\r\n" % port, downloader._err.getvalue()) 
            callback = reactor.calledMethods[-1].args[1]
            callback() # startProcess
            callback = reactor.calledMethods[-1].args[1]
            callback() # _processOne.next -> HTTP GET
            sleep(0.01)
            self.assertEquals("GET /path?argument=value HTTP/1.0\r\n\r\n", msgs[0])
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''
            callback() # _processOne.next -> addProcess
            self.assertEquals(['buildRequest', 'buildRequest', 'handle'], [m.name for m in observer.calledMethods])
            callback()
            self.assertReactorState(reactor)

    def testDriver(self):
        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            downloader, observer, reactor = self.getDownloader("localhost", port)
            self.assertEquals(1, reactor.calledMethods[0].args[0])
            callback = reactor.calledMethods[0].args[1]
            callback() # connect
            callback = reactor.calledMethods[1].args[1]
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv
            callback() # sok.recv
            self.assertEquals('addProcess', reactor.calledMethods[5].name)
            process = reactor.calledMethods[5].args[0]
            try:
                while True:
                    process()
            except StopIteration:
                pass
            self.assertEquals('removeProcess', reactor.calledMethods[6].name)
            self.assertReactorState(reactor)
             
    def testShortenErrorMessage(self):
        from meresco.components.periodicdownload import shorten
        longMessage = "a"*100000
        self.assertTrue(len(shorten(longMessage)) < len(longMessage)/10)

    def testAutoStartOff(self):
        reactor = CallTrace("reactor")
        downloader = PeriodicDownload(reactor, 'host', 12345, autoStart=False)
        downloader.observer_init()
        self.assertEquals([], reactor.calledMethodNames())

    def testPauseResume(self):
        # Copy/Paste of 'def server(...)'
        # could not match both servers, some test keep 'hanging'
        @contextmanager
        def server2(responses, bufsize=4096):
            port = randint(10000,60000)
            start = Event()
            messages = []
            def serverThread():
                s = socket()
                s.bind(('127.0.0.1', port))
                s.listen(0)
                start.set()
                while responses:
                    try:
                        connection, address = s.accept()
                        msg = connection.recv(bufsize)
                        messages.append(msg)
                        response = responses.pop()
                        connection.send(response)
                        connection.close()
                    except:
                        pass
            thread = Thread(None, serverThread)
            thread.start()
            start.wait()
            yield port, messages
            thread.join()
            responsesLeft = len(responses)
            if False and responsesLeft > 0:
                del responses[:]
                sok = socket()
                sok.connect(('127.0.0.1', port))
                sok.close()
            assert responsesLeft == 0, "Expected no more responses, but %s left." % responsesLeft

        reactor = Reactor()
        stepping = [True]
        def uit():
            stepping[0] = False
        reactor.addTimer(2, uit)

        receivedData = []
        
        class TestHandler(Observable):
            def __init__(self):
                Observable.__init__(self)
                self._t0 = time()
            def buildRequest(self):
                return 'request'
            def handle(self, data):
                receivedData.append(('%.1fs' % (time() - self._t0), data))
                if len(receivedData) >= 3:
                    receivedData.append('PAUSE')
                    self.call.pause()
                return
                yield

        with server2(["HTTP/1.0 200 Ok\r\n\r\nmessage"]*5) as (port, msgs):
            download = PeriodicDownload(reactor, '127.0.0.1', port, period=0.1, err=StringIO())
            dna = be(
            (Observable(),
                (download,
                    (TestHandler(),
                        (download,)
                    )
                )
            ))
            list(compose(dna.once.observer_init()))

            reactor.addTimer(1, lambda: dna.call.resume())
            while stepping[0]:
                reactor.step()
            self.assertEquals('message', urlopen('http://127.0.0.1:%s/request' % port).read())
        self.assertEquals([
            ('0.1s', 'message'),
            ('0.2s', 'message'),
            ('0.3s', 'message'),
            'PAUSE',
            ('1.1s', 'message'),
            'PAUSE',
            ], receivedData)

    
    def getDownloader(self, host, port, period=1, handleGenerator=None):
        handleGenerator = handleGenerator or (x for x in 'X')
        self._reactor = CallTrace("reactor")
        self._downloader = PeriodicDownload(self._reactor, host, port, period=period, prio=0, err=StringIO())
        self._observer = CallTrace("observer", methods={'handle': lambda data: handleGenerator})
        self._observer.returnValues["buildRequest"] = "GET /path?argument=value HTTP/1.0\r\n\r\n"
        self._downloader.addObserver(self._observer)
        self._downloader.observer_init()
        self.assertEquals(period, self._reactor.calledMethods[0].args[0])
        return self._downloader, self._observer, self._reactor

    def doConnect(self):
        callback = self._reactor.calledMethods[0].args[1]
        callback() # startProcess -> tryConnect
        callback = self._reactor.calledMethods[1].args[1]
        return callback # _processOne.next

    def assertReactorState(self, reactor):
        names = [m.name for m in reactor.calledMethods]
        for what in ['Writer', 'Reader', 'Process']: 
            self.assertEquals(len([n for n in names if n == 'add%s' % what]),
                len([n for n in names if n == 'remove%s' % what]), 
                'Expected same amount of add and remove for %s' % what)

HTTP_SEPARATOR = 2 * CRLF
STATUSLINE = """HTTP/1.0 200 OK """ + HTTP_SEPARATOR
STATUSLINE_ALTERNATIVE = """HTTP/1.1 200 ok """ + HTTP_SEPARATOR

EMBEDDED_RECORD = '<record>ignored</record>'
BODY = """<aap:noot xmlns:aap="mies">%s</aap:noot>"""
ONE_RECORD = BODY % (EMBEDDED_RECORD) 
TWO_RECORDS = BODY % (EMBEDDED_RECORD * 2) 
RESPONSE_ONE_RECORD = STATUSLINE + ONE_RECORD 
RESPONSE_TWO_RECORDS = STATUSLINE + TWO_RECORDS 

