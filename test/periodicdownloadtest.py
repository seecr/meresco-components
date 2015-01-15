## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011, 2013-2014 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012, 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

import warnings
from contextlib import contextmanager
from random import randint
from threading import Event, Thread
from socket import socket, socketpair, error as SocketError, AF_UNIX, SHUT_RDWR
from errno import EAGAIN
from io import StringIO
from urllib.request import urlopen
from time import time, sleep
from itertools import count

from seecr.test import SeecrTestCase, CallTrace
from seecr.test.io import stderr_replaced
from seecr.test.utils import ignoreLineNumbers

from weightless.core import be, compose, consume
from weightless.io import Reactor, Suspend

from meresco.core import Observable

from meresco.components.http.utils import CRLF
from meresco.components import PeriodicDownload, Schedule
from http.server import BaseHTTPRequestHandler
from socketserver import TCPServer


@contextmanager
def server(responses, bufsize=4096, sleepWhile=None):
    sleepWhile = sleepWhile or (lambda: False)
    port = randint(10000,60000)
    start = Event()
    end = Event()
    messages = []
    def serverThread():
        with socket() as s: 
            s.bind(('127.0.0.1', port))
            s.listen(0)
            start.set()
            closeLater = []
            while not end.isSet():
                try:
                    connection, address = s.accept()
                    if end.isSet():
                        closeLater.append(connection)
                        break
                    msg = connection.recv(bufsize)
                    messages.append(msg)
                    response = responses.pop(0)
                    if not response is DROP_CONNECTION:
                        def respond(connection=connection, response=response):
                            while sleepWhile():
                                sleep(0.05)
                            if type(response) is str:
                                response = response.encode()
                            connection.send(response)
                            connection.close()
                        t = Thread(None, respond)
                        t.daemon = True
                        t.start()
                    else:
                        closeLater.append(connection)
                except:
                    from traceback import print_exc; print_exc()
                    pass
        for s in closeLater:
            s.close()
    thread = Thread(None, serverThread)
    thread.daemon = True
    thread.start()
    start.wait()
    yield port, messages
    end.set()
    with socket() as sokToBustOutOfAccept:
        try:
            sokToBustOutOfAccept.connect(("localhost", port))
        except (ConnectionRefusedError, ConnectionResetError):
            pass

class PeriodicDownloadTest(SeecrTestCase):

    def testOne(self):
        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port)
            self.assertEqual('addTimer', reactor.calledMethods[0].name)
            self.assertEqual(1, reactor.calledMethods[0].args[0])
            callback = reactor.calledMethods[0].args[1]
            callback() # connect
            self.assertEqual('addWriter', reactor.calledMethods[1].name)
            callback = reactor.calledMethods[1].args[1]
            callback() # HTTP GET
            sleep(0.01)
            self.assertEqual(b"GET", msgs[0][:3])
            self.assertEqual('removeWriter', reactor.calledMethods[2].name)
            self.assertEqual('addReader', reactor.calledMethods[3].name)
            self.assertEqual(0, reactor.calledMethods[3].kwargs['prio'])
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv
            callback() # sok.recv
            self.assertEqual("", downloader._err.getvalue())
            self.assertEqual('buildRequest', observer.calledMethods[0].name)
            self.assertEqual({'Host': 'localhost'}, observer.calledMethods[0].kwargs['additionalHeaders'])
            callback() # addProcess
            self.assertEqual('handle', observer.calledMethods[1].name)
            self.assertEqual(0, len(observer.calledMethods[1].args))
            self.assertEqual(['data'], list(observer.calledMethods[1].kwargs.keys()))
            self.assertEqualsWS(ONE_RECORD, observer.calledMethods[1].kwargs['data'])
            callback()
            self.assertReactorStateClean(reactor)

    def testOneWithProxy(self):
        request = []
        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            proxyServer(port + 1, request)
            downloader, observer, reactor = self._prepareDownloader("localhost", port, proxyServer="http://localhost:%s" % (port + 1))
            self.assertEqual('addTimer', reactor.calledMethods[0].name)
            self.assertEqual(1, reactor.calledMethods[0].args[0])
            callback = reactor.calledMethods[0].args[1]
            callback() # connect
            sleep(0.5)
            self.assertEqual('addWriter', reactor.calledMethods[1].name)
            callback = reactor.calledMethods[1].args[1]
            callback() #proxy connect
            sleep(0.5)
            self.assertEqual(['addTimer', 'addWriter', 'removeWriter', 'addReader'], reactor.calledMethodNames())
            callback = reactor.calledMethods[-1].args[1]
            callback() #proxy recv
            sleep(0.01)
            self.assertEqual(b"GET", msgs[0][:3])
            self.assertEqual('addReader', reactor.calledMethods[-1].name)
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv
            callback() # sok.recv
            self.assertEqual("", downloader._err.getvalue())
            self.assertEqual('buildRequest', observer.calledMethods[0].name)
            self.assertEqual({'Host': 'localhost'}, observer.calledMethods[0].kwargs['additionalHeaders'])
            callback() # addProcess
            self.assertEqual('handle', observer.calledMethods[1].name)
            self.assertEqual(0, len(observer.calledMethods[1].args))
            self.assertEqual(['data'], list(observer.calledMethods[1].kwargs.keys()))
            self.assertEqualsWS(ONE_RECORD, observer.calledMethods[1].kwargs['data'])
            callback()
            self.assertEqual(1, len(request))
            self.assertReactorStateClean(reactor)

    def testNoConnectionPossibleWithNonIntegerPort(self):
        downloader, observer, reactor = self._prepareDownloader("some.nl", 'no-port')
        callback = reactor.calledMethods[0].args[1]
        callback() # connect
        self.assertEqual("%s: an integer is required (got type str)\n" % repr(downloader), downloader._err.getvalue())
        self.assertReactorStateClean(reactor)

    def testNoConnectionPossible(self):
        downloader, observer, reactor = self._prepareDownloader("localhost", 8899)
        callback = reactor.calledMethods[0].args[1]
        callback() # connect
        reactor.exceptions['removeWriter'] = IOError("error in sockopt") ## Simulate IOError as raised from sok.getsockopt
        callback = reactor.calledMethods[1].args[1]
        callback() # HTTP GET
        self.assertEqual("%s: error in sockopt\n" % repr(downloader), downloader._err.getvalue())
        del reactor.exceptions['removeWriter']
        self.assertEqual('addTimer', reactor.calledMethods[-1].name)
        self.assertEqual(30, reactor.calledMethods[-1].args[0])

        self.assertReactorStateClean(reactor)

        callback = reactor.calledMethods[-1].args[1]
        callback() # connect
        self.assertEqual("addWriter", reactor.calledMethods[-1].name)
        self.assertEqual("%s: error in sockopt\n" % downloader, downloader._err.getvalue()) # remains 1 error

    def testVerboseDeprecationWarning(self):
        with stderr_replaced() as s:
            PeriodicDownload(reactor='x', host='x', port='x')
            result = s.getvalue()
            self.assertEqual('', result)

        with warnings.catch_warnings():
            warnings.simplefilter("default")
            with stderr_replaced() as s:
                PeriodicDownload(reactor='x', host='x', port='x', verbose=True)
                result = s.getvalue()
                self.assertTrue('DeprecationWarning: Verbose flag is deprecated' in result, result)

    def testErrorResponse(self):
        with server(['HTTP/1.0 400 Error\r\nContent-Type: text/plain\r\n\r\nIllegal Request']) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port)
            callback = reactor.calledMethods[0].args[1]
            callback() # connect
            callback = reactor.calledMethods[1].args[1]
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv

            callback() # yield After Error

            self.assertEqual("%s: Unexpected response: HTTP/1.0 400 Error\r\nContent-Type: text/plain\r\n\r\nIllegal Request\nFor request: GET /path?argument=value HTTP/1.0\r\n\r\n" % repr(downloader), downloader._err.getvalue())
            self.assertEqual(['buildRequest'], [m.name for m in observer.calledMethods])
            self.assertReactorStateClean(reactor)

    def testInvalidPortConnectionRefused(self):
        downloader, observer, reactor = self._prepareDownloader("localhost", 88)
        callback = reactor.calledMethods[0].args[1]
        callback() # startProcess
        self.assertEqual("addWriter", reactor.calledMethods[1].name)
        callback = reactor.calledMethods[1].args[1]
        callback() # _processOne.next
        self.assertEqual("removeWriter", reactor.calledMethods[2].name)
        self.assertEqual("addTimer", reactor.calledMethods[3].name)
        self.assertEqual("%s: Connection refused.\n" % downloader, downloader._err.getvalue())
        self.assertReactorStateClean(reactor)

    def testInvalidHost(self):
        strangeHost = "UEYR^$*FD(#>NDJ.khfd9.(*njnd.nl"
        downloader, observer, reactor = self._prepareDownloader(strangeHost, 88)
        callback = reactor.calledMethods[0].args[1]
        callback() # connect
        self.assertEqual('addTimer', reactor.calledMethods[-1].name)
        nameOrServiceNotKnown = ("%s: -2: Name or service not known\n" % downloader ==  downloader._err.getvalue())
        noAddressAssociatedWithHost = ("%s: -5: No address associated with hostname\n" % downloader == downloader._err.getvalue())
        self.assertTrue(nameOrServiceNotKnown or noAddressAssociatedWithHost, downloader._err.getvalue())
        self.assertReactorStateClean(reactor)

    def testInvalidHostConnectionRefused(self):
        downloader, observer, reactor = self._prepareDownloader("127.0.0.255", 9876)
        callback = reactor.calledMethods[0].args[1]
        callback() # startProcess
        self.assertEqual("addWriter", reactor.calledMethods[1].name)
        callback = reactor.calledMethods[1].args[1]
        callback() # _processOne.next
        self.assertEqual("%s: Connection refused.\n" % downloader, downloader._err.getvalue())
        self.assertEqual("removeWriter", reactor.calledMethods[2].name)
        self.assertEqual("addTimer", reactor.calledMethods[3].name)
        self.assertReactorStateClean(reactor)

    def testSuccess(self):
        with server([RESPONSE_TWO_RECORDS]) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port)
            self.assertEqual(1, downloader.getState().schedule.secondsFromNow())
            callback = self.doConnect() # _processOne.next
            callback() # _processOne.next -> HTTP GET
            self.assertEqual('buildRequest', observer.calledMethods[0].name)
            sleep(0.01)
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''
            callback() # addProcess
            self.assertEqual("", downloader._err.getvalue())
            self.assertEqual('handle', observer.calledMethods[1].name)
            self.assertEqualsWS(TWO_RECORDS, observer.calledMethods[1].kwargs['data'])
            self.assertEqual('addProcess', reactor.calledMethods[-1].name)
            callback() # _processOne.next
            self.assertEqual('removeProcess', reactor.calledMethods[-2].name)
            self.assertEqual('addTimer', reactor.calledMethods[-1].name)
            self.assertReactorStateClean(reactor)

    def testSuccessWithSuspend(self):
        suspendObject = Suspend()
        with server([RESPONSE_TWO_RECORDS]) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port, handleGenerator=(x for x in ['X', suspendObject]))
            self.assertEqual(1, downloader.getState().schedule.secondsFromNow())
            callback = self.doConnect() # _processOne.next
            callback() # _processOne.next -> HTTP GET
            self.assertEqual('buildRequest', observer.calledMethods[0].name)
            sleep(0.01)
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''
            callback() # addProcess
            self.assertEqual("", downloader._err.getvalue())
            self.assertEqual('handle', observer.calledMethods[1].name)
            self.assertEqualsWS(TWO_RECORDS, observer.calledMethods[1].kwargs['data'])
            self.assertEqual('addProcess', reactor.calledMethods[-1].name)
            callback = reactor.calledMethods[-1].args[0]
            callback()
            self.assertEqual('suspend', reactor.calledMethods[-1].name)
            suspendObject.resume("resume response")
            self.assertEqual('resumeProcess', reactor.calledMethods[-1].name)
            callback()
            self.assertEqual('removeProcess', reactor.calledMethods[-2].name)
            self.assertEqual('addTimer', reactor.calledMethods[-1].name)
            self.assertReactorStateClean(reactor)

    def testRaiseInHandle(self):
        def handleGenerator():
            yield 'first'
            raise Exception('xcptn')
            yield

        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port, handleGenerator=handleGenerator())
            callback = self.doConnect() # _processOne.next
            callback() # _processOne.next -> HTTP GET
            self.assertEqual('buildRequest', observer.calledMethods[0].name)
            sleep(0.01)
            self.assertEqual([b'GET /path?argument=value HTTP/1.0\r\n\r\n'], msgs) # message received, getting response
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''; then addProcess
            callback() # first self.all.handle(data=body) -> 1st response

            result = downloader._err.getvalue()
            self.assertEqual('', result)

            callback() # 2nd response / raise Exception(...)
            result = downloader._err.getvalue()
            self.assertTrue('Traceback' in result, result)

            self.assertTrue(ignoreLineNumbers(result).startswith(ignoreLineNumbers("""%s: Traceback (most recent call last):
  File "%%(periodicdownload.py)s", line 104, in _processOne""" % repr(downloader) % fileDict)), result)

            tracebackTail = ignoreLineNumbers("""  File "%(__file__)s", line 314, in handleGenerator
    raise Exception('xcptn')
Exception: xcptn
Error while processing response: HTTP/1.0 200 OK\r\n\r\n<aap:noot xmlns:aap="mies"><record>ignored</record></aap:noot>
For request: GET /path?argument=value HTTP/1.0\r\n\r\n""" % fileDict)

            self.assertTrue(tracebackTail in ignoreLineNumbers(result), result) 

            self.assertEqual('removeProcess', reactor.calledMethods[-2].name)
            self.assertEqual('addTimer', reactor.calledMethods[-1].name)
            self.assertReactorStateClean(reactor)

    def testAssertionErrorReraised(self):
        with server([RESPONSE_TWO_RECORDS]) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port)
            def raiseAssertionError(*args, **kwargs):
                assert True == False, "Somewhat but not quite unexpected: True not equal to False"
            observer.methods['handle'] = raiseAssertionError

            self.assertEqual(1, downloader.getState().schedule.secondsFromNow())
            callback = self.doConnect() # _processOne.next
            callback() # _processOne.next -> HTTP GET
            self.assertEqual('buildRequest', observer.calledMethods[0].name)
            sleep(0.01)
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''
            try:
                callback() # addProcess
                self.assertEqual('', self._downloader._err.getvalue())
                self.fail('should not get here')
            except AssertionError as e:
                self.assertEqual('Somewhat but not quite unexpected: True not equal to False', str(e))

    def testSuccessHttp1dot1Server(self):
        with server([STATUSLINE_ALTERNATIVE + ONE_RECORD]) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port)
            callback = self.doConnect()
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv
            callback() # recv = ''
            callback() # addProcess
            self.assertEqual("", downloader._err.getvalue())
            self.assertEqual('buildRequest', observer.calledMethods[0].name)
            self.assertEqualsWS(ONE_RECORD, observer.calledMethods[1].kwargs['data'])
            callback()
            self.assertReactorStateClean(reactor)

    def testPeriod(self):
        with server([RESPONSE_TWO_RECORDS, 'HTTP/1.0 400 Error\r\n\r\nIllegal Request']) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port, period=2)
            callback = self.doConnect()
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[-1].args[1]
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''
            callback() # _processOne.next
            self.assertEqual('addProcess', reactor.calledMethods[-1].name)
            callback = reactor.calledMethods[-1].args[0]
            callback() # _processOne.next
            self.assertEqual('addTimer', reactor.calledMethods[-1].name)
            self.assertEqual(2, reactor.calledMethods[-1].args[0])

            callback = reactor.calledMethods[-1].args[1]
            callback() # startProcess
            callback = reactor.calledMethods[-1].args[1]
            callback() # _processOne.next -> HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[-1].args[1]
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''
            # error status
            self.assertEqual('addTimer', reactor.calledMethods[-1].name)
            self.assertEqual(30, reactor.calledMethods[-1].args[0])
            self.assertReactorStateClean(reactor)

    def testRecoveringAfterDroppedConnection(self):
        with server([DROP_CONNECTION, RESPONSE_ONE_RECORD]) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port)
            callback = self.doConnect()
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[-1].args[1]
            callback() # _processOne.next -> sok.recv
            self.assertEqual("%s: Receive error: 11: Resource temporarily unavailable\nFor request: GET /path?argument=value HTTP/1.0\r\n\r\n" % repr(downloader), downloader._err.getvalue())
            callback = reactor.calledMethods[-1].args[1]
            callback() # startProcess
            callback = reactor.calledMethods[-1].args[1]
            callback() # _processOne.next -> HTTP GET
            sleep(0.01)
            self.assertEqual(b"GET /path?argument=value HTTP/1.0\r\n\r\n", msgs[0])
            callback() # _processOne.next -> sok.recv
            callback() # _processOne.next -> recv = ''
            callback() # _processOne.next -> addProcess
            self.assertEqual(['buildRequest', 'buildRequest', 'handle'], [m.name for m in observer.calledMethods])
            callback()
            self.assertReactorStateClean(reactor)

    def testDriver(self):
        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port)
            self.assertEqual(1, reactor.calledMethods[0].args[0])
            callback = reactor.calledMethods[0].args[1]
            callback() # connect
            callback = reactor.calledMethods[1].args[1]
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[3].args[1]
            callback() # sok.recv
            callback() # sok.recv
            self.assertEqual('addProcess', reactor.calledMethods[5].name)
            process = reactor.calledMethods[5].args[0]
            try:
                while True:
                    process()
            except StopIteration:
                pass
            self.assertEqual('removeProcess', reactor.calledMethods[6].name)
            self.assertReactorStateClean(reactor)

    def testShortenErrorMessage(self):
        from meresco.components.periodicdownload import _shorten
        longMessage = "a"*100000
        self.assertTrue(len(_shorten(longMessage)) < len(longMessage)/10)

    def testAutoStartOff(self):
        reactor = CallTrace("reactor")
        downloader = PeriodicDownload(reactor, 'host', 12345, autoStart=False)
        downloader.observer_init()
        self.assertEqual([], reactor.calledMethodNames())

    def testHostAndPortRequiredUnlessAutostartFalse(self):
        reactor = CallTrace("reactor")
        self.assertRaises(ValueError, lambda: PeriodicDownload(reactor))
        self.assertRaises(ValueError, lambda: PeriodicDownload(reactor, host='example.com'))
        self.assertRaises(ValueError, lambda: PeriodicDownload(reactor, port=123))
        PeriodicDownload(reactor, autoStart=False)

    def testRepr(self):
        reactor = CallTrace("reactor")
        downloader = PeriodicDownload(reactor, autoStart=False)
        self.assertEqual("PeriodicDownload(schedule=Schedule(period=1))", repr(downloader))
        reactor = CallTrace("reactor")
        downloader = PeriodicDownload(reactor, host='example.com', port=80)
        self.assertEqual("PeriodicDownload(host='example.com', port=80, schedule=Schedule(period=1))", repr(downloader))
        downloader = PeriodicDownload(reactor, name="theName", autoStart=False)
        self.assertEqual("PeriodicDownload(name='theName', schedule=Schedule(period=1))", repr(downloader))

    def testResumeDuringSuspend(self):
        reactor = Reactor()
        stepping = [True]
        def uit():
            stepping[0] = False
        reactor.addTimer(0.5, uit)
        suspended = [True]

        def handle(data):
            for i in range(5):
                yield 'ignore'

        err = StringIO()
        with server(["HTTP/1.0 200 OK\r\n\r\nmessage"]*20, sleepWhile=lambda: suspended[0]) as (port, msgs):
            download = PeriodicDownload(reactor, '127.0.0.1', port, schedule=Schedule(period=0.01), err=err)
            observer = CallTrace(methods={'handle': handle}, returnValues={'buildRequest': b'request'}, emptyGeneratorMethods=['handle'])
            dna = be(
            (Observable(),
                (download,
                    (observer,),
                )
            ))
            list(compose(dna.once.observer_init()))

            reactor.addTimer(0.1, lambda: download.pause())
            reactor.addTimer(0.2, lambda: download.resume())
            def unsuspend():
                suspended[0] = False
            reactor.addTimer(0.3, unsuspend)
            while stepping[0]:
                reactor.step()
        self.assertFalse('Process is already in processes' in err.getvalue())

    def testPauseResume(self):
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
            def buildRequest(self, additionalHeaders=None):
                return b'request'
            def handle(self, data):
                receivedData.append(('%.1fs' % (time() - self._t0), data))
                if len(receivedData) >= 3:
                    receivedData.append('PAUSE')
                    self.call.pause()
                return
                yield

        with server(["HTTP/1.0 200 OK\r\n\r\nmessage"]*5) as (port, msgs):
            download = PeriodicDownload(reactor, '127.0.0.1', port, schedule=Schedule(period=0.1), err=StringIO())
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
            with urlopen("http://127.0.0.1:%s/request" % port) as strm:
                self.assertEqual(b'message', strm.read())
        self.assertEqual([
            ('0.1s', 'message'),
            ('0.2s', 'message'),
            ('0.3s', 'message'),
            'PAUSE',
            ('1.1s', 'message'),
            'PAUSE',
            ], receivedData)

    def testPauseResumeWithError(self):
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
            def buildRequest(self, additionalHeaders=None):
                return b'request'
            def handle(self, data):
                receivedData.append(('%.1fs' % (time() - self._t0), data))
                if len(receivedData) >= 2:
                    receivedData.append('PAUSE')
                    self.call.pause()
                    raise ValueError('You shall not pass!')
                return
                yield

        with server(["HTTP/1.0 200 OK\r\n\r\nmessage"]*4) as (port, msgs):
            download = PeriodicDownload(reactor, '127.0.0.1', port, schedule=Schedule(period=0.1), err=StringIO())
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
            with urlopen('http://127.0.0.1:%s/request' % port) as strm:
                self.assertEqual(b'message', strm.read())
        self.assertEqual([
            ('0.1s', 'message'),
            ('0.2s', 'message'),
            'PAUSE',
            ('1.1s', 'message'),
            'PAUSE',
            ], receivedData)

    def testResumeAfterDroppedConnectionPauseAndRefusedConnection(self):
        with server([DROP_CONNECTION]) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port)
            callback = self.doConnect()
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[-1].args[1]
            callback() # _processOne.next -> sok.recv
            self.assertEqual("%s: Receive error: 11: Resource temporarily unavailable\nFor request: GET /path?argument=value HTTP/1.0\r\n\r\n" % repr(downloader), downloader._err.getvalue())

        self.assertEqual('addTimer', reactor.calledMethods[-1].name)
        callback = reactor.calledMethods[-1].args[1]
        downloader.pause()
        downloader.setDownloadAddress('localhost', 11111)
        callback() # startProcess
        self.assertEqual('addWriter', reactor.calledMethods[-1].name)
        callback = reactor.calledMethods[-1].args[1]
        downloader._err.truncate(0)
        downloader._err.seek(0)
        callback()
        self.assertEqual('removeWriter', reactor.calledMethods[-1].name)
        self.assertEqual("%s: Connection refused.\n" % repr(downloader), downloader._err.getvalue())

        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            downloader.setDownloadAddress('localhost', port)
            downloader.resume()
            self.assertEqual('addTimer', reactor.calledMethods[-1].name)

    def testGetState(self):
        reactor = CallTrace("reactor")
        downloader = PeriodicDownload(reactor, 'host', 12345, name='theName')
        s = downloader.getState()

        self.assertEqual('theName', s.name)
        self.assertEqual('host', s.host)
        self.assertEqual(12345, s.port)
        self.assertEqual(False, s.paused)

        reactor = CallTrace("reactor")
        downloader = PeriodicDownload(reactor, 'unhost', 54321, name='anotherName', autoStart=False)
        s = downloader.getState()

        self.assertEqual('anotherName', s.name)
        self.assertEqual('unhost', s.host)
        self.assertEqual(54321, s.port)
        self.assertEqual(True, s.paused)

        self.assertEqual([], reactor.calledMethodNames())

    def testSetDownloadAddress(self):
        reactor = CallTrace("reactor")
        downloader = PeriodicDownload(reactor, host=None, port=None, autoStart=False)
        downloader.setDownloadAddress(host='host', port=12345)
        s = downloader.getState()
        self.assertEqual('host', s.host)
        self.assertEqual(12345, s.port)
        downloader.setDownloadAddress(host='anotherHost', port=54321)
        s = downloader.getState()
        self.assertEqual('anotherHost', s.host)
        self.assertEqual(54321, s.port)

        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port)
            self.assertEqual('addTimer', reactor.calledMethods[0].name)
            callback = reactor.calledMethods[-1].args[1]
            callback() # connect
            callback = reactor.calledMethods[-1].args[1]
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[-1].args[1]
            callback() # sok.recv
            callback() # sok.recv
            callback() # addProcess
            self.assertEqualsWS(ONE_RECORD, observer.calledMethods[1].kwargs['data'])
            callback()
            self.assertReactorStateClean(reactor)
            oldPort = port
        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            self.assertNotEqual(oldPort, port)
            downloader.setDownloadAddress(host='localhost', port=port)
            self._observer.methods['handle'] = lambda data: (x for x in 'X')
            callback = reactor.calledMethods[-1].args[1]
            callback() # connect
            callback = reactor.calledMethods[-1].args[1]
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[-1].args[1]
            callback() # sok.recv
            callback() # sok.recv
            callback() # addProcess
            self.assertEqualsWS(ONE_RECORD, observer.calledMethods[1].kwargs['data'])
            callback()
            self.assertReactorStateClean(reactor)

    def testSetPeriod(self):
        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            downloader, observer, reactor = self._prepareDownloader("localhost", port)
            self.assertEqual('addTimer', reactor.calledMethods[0].name)
            self.assertEqual(1, reactor.calledMethods[-1].args[0])
            downloader.setSchedule(Schedule(period=42))
            self.assertEqual(42, downloader.getState().schedule.secondsFromNow())
            self.assertEqual('removeTimer', reactor.calledMethods[-2].name)
            self.assertEqual('timerObject0', reactor.calledMethods[-2].args[0])
            self.assertEqual('addTimer', reactor.calledMethods[-1].name)
            self.assertEqual(42, reactor.calledMethods[-1].args[0])

            callback = reactor.calledMethods[-1].args[1]
            callback() # connect
            callback = reactor.calledMethods[-1].args[1]
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[-1].args[1]
            callback() # sok.recv
            callback() # sok.recv
            callback() # addProcess
            self.assertEqualsWS(ONE_RECORD, observer.calledMethods[1].kwargs['data'])
            callback()
            self.assertReactorStateClean(reactor)
            self.assertEqual('addTimer', reactor.calledMethods[-1].name)
            self.assertEqual(42, reactor.calledMethods[-1].args[0])

    def testSendOnClosedSocketRetries(self):
        sok = socket()
        sok.close()
        reactor = CallTrace('reactor')
        observer = CallTrace('observer', returnValues={'buildRequest': b'request'})
        downloader = PeriodicDownload(reactor, host='localhost', port=9999, err=StringIO())
        downloader.addObserver(observer)
        def mockTryConnect(host, port, proxyServer=None):
            raise StopIteration(sok)
            yield
        downloader._tryConnect = mockTryConnect
        list(compose(downloader._processOne()))
        self.assertEqual(['addTimer'], reactor.calledMethodNames())

    def testHalfClosedSocketAfterTryConnectResultsInEmptyData(self):
        # Kindof odd, but tests try/except around clientSocket.shutdown()
        # which gives an ENOTCONN / Transport endpoint is not connected.
        sokClient = socket()
        sokClient.setblocking(0)
        sokServer = socket()
        sokServer.setblocking(0)
        serverHostPort = ('127.0.0.1', randint(10000,60000))
        sokServer.bind(serverHostPort)
        sokServer.listen(0)
        sleep(0.01)
        try:
            sokClient.connect(serverHostPort)
        except SocketError as xxx_todo_changeme1:
            (errno, msg) = xxx_todo_changeme1.args
            self.assertEqual('Operation now in progress', msg)
        sleep(0.01)
        connectionSok, _ = sokServer.accept()

        sleep(0.01)
        # Half-Close or Close makes no difference here.
        sokServer.shutdown(SHUT_RDWR)
        sokServer.close()
        connectionSok.shutdown(SHUT_RDWR)
        connectionSok.close()
        sleep(0.01)

        reactor = CallTrace('reactor')
        observer = CallTrace('observer', returnValues={'buildRequest': b'request'})
        downloader = PeriodicDownload(reactor, host='localhost', port=9999, err=StringIO())
        downloader.addObserver(observer)
        def mockTryConnect(host, port, proxyServer=None):
            raise StopIteration(sokClient)
            yield
        downloader._tryConnect = mockTryConnect
        processOne = downloader._processOne()
        downloader._currentProcess = processOne
        consume(processOne)
        self.assertEqual(['addReader', 'removeReader', 'addTimer'], reactor.calledMethodNames())

    def testSocketNotShutdownForWriteAfterWriteDone(self):
        # A.k.a don't send TCP FIN until HTTP Request finished please ;-)
        client, server = socketpair(AF_UNIX)
        client.setblocking(0)
        server.setblocking(0)
        try:
            reactor = CallTrace()
            class BuildRequest(object):
                def buildRequest(self, additionalHeaders=None):
                    # A.k.a. not fitting into the buffer.
                    return b'small request'
            downloader = PeriodicDownload(reactor, host='localhost', port=9999, err=StringIO())
            def mockTryConnect(host, port, proxyServer=None):
                raise StopIteration(client)
                yield
            downloader._tryConnect = mockTryConnect
            downloader._currentProcess = compose(downloader._processOne())
            downloader.addObserver(BuildRequest())

            next(downloader._currentProcess)
            self.assertEqual(['addReader'], reactor.calledMethodNames())
            sleep(0.01)
            self.assertEqual(b'small request', server.recv(4096))

            sleep(0.01)
            try:
                _ = server.recv(1)
            except SocketError as e:
                (errno, msg) = e.args
                self.assertEqual(EAGAIN, errno)
            else:
                self.fail('TCP connection must remain open until the request is finished.')

            # cleanup
            reactor.calledMethods.reset()
            list(downloader._currentProcess)
            self.assertEqual(['removeReader', 'addTimer'], reactor.calledMethodNames())
        finally:
            server.close()

    def testShortRequestSendWithoutReactor(self):
        client, server = socketpair(AF_UNIX)
        client.setblocking(0)
        try:
            reactor = CallTrace()
            class BuildRequest(object):
                def buildRequest(self, additionalHeaders=None):
                    # A.k.a. not fitting into the buffer.
                    return b'small request'
            downloader = PeriodicDownload(reactor, host='localhost', port=9999, err=StringIO())
            def mockTryConnect(host, port, proxyServer=None):
                raise StopIteration(client)
                yield
            downloader._tryConnect = mockTryConnect
            downloader._currentProcess = compose(downloader._processOne())
            downloader.addObserver(BuildRequest())

            next(downloader._currentProcess)
            self.assertEqual(['addReader'], reactor.calledMethodNames())
            self.assertEqual(b'small request', server.recv(4096))

            reactor.calledMethods.reset()
            list(downloader._currentProcess)
            self.assertEqual(['removeReader', 'addTimer'], reactor.calledMethodNames())
        finally:
            client.close()
            server.close()

    def testReallyLargeRequestSendWithReactor(self):
        def readall():
            data = None
            count = 0
            while data != '':
                try:
                    data = server.recv(4096)
                    count += 1
                except SocketError as xxx_todo_changeme:
                    (errno, msg) = xxx_todo_changeme.args
                    self.assertEqual(EAGAIN, errno)
                    break
            self.assertTrue(data)
            return count

        client, server = socketpair(AF_UNIX)
        server.setblocking(0)
        client.setblocking(0)
        reactor = CallTrace()
        class BuildRequest(object):
            def buildRequest(self, additionalHeaders=None):
                # A.k.a. not fitting into the buffer.
                return (b'x' * (256 * 1024))
        try:
            downloader = PeriodicDownload(reactor, host='localhost', port=9999, err=StringIO())
            def mockTryConnect(host, port, proxyServer=None):
                raise StopIteration(client)
                yield
            downloader._tryConnect = mockTryConnect
            downloader._currentProcess = compose(downloader._processOne())
            downloader.addObserver(BuildRequest())

            next(downloader._currentProcess)
            self.assertEqual(['addWriter'], reactor.calledMethodNames())
            addWriterCB = reactor.calledMethods[0].args[1]
            self.assertEqual(addWriterCB, downloader._currentProcess.__next__)

            count = readall()

            reactor.calledMethods.reset()
            next(downloader._currentProcess)
            self.assertEqual([], reactor.calledMethodNames())

            count = readall()

            reactor.calledMethods.reset()
            next(downloader._currentProcess)
            self.assertEqual(['removeWriter', 'addReader'], reactor.calledMethodNames())

            reactor.calledMethods.reset()
            list(downloader._currentProcess)
            self.assertEqual(['removeReader', 'addTimer'], reactor.calledMethodNames())
        finally:
            client.close()
            server.close()

    def testNoBuildRequestSleeps(self):
        reactor = CallTrace('reactor')
        observer = CallTrace('observer', returnValues={'buildRequest': None})
        downloader = PeriodicDownload(reactor, host='localhost', port=9999, err=StringIO())
        downloader.addObserver(observer)

        downloader._startProcess()
        self.assertEqual(['addTimer'], reactor.calledMethodNames())

    def testUseBuildRequestHostAndPort(self):
        with server([RESPONSE_ONE_RECORD]) as (port, msgs):
            reactor = CallTrace('reactor')
            observer = CallTrace('observer', returnValues={'buildRequest': dict(host='localhost', port=port, request=b'GET /path HTTP/1.0\r\n\r\n')}, emptyGeneratorMethods=['handle'])
            observer.methods['handle'] = lambda data: (x for x in 'X')
            downloader = PeriodicDownload(reactor, err=StringIO(), autoStart=False)
            downloader.addObserver(observer)
            downloader._startProcess()
            callback = reactor.calledMethods[-1].args[1]
            callback() # HTTP GET
            sleep(0.01)
            callback = reactor.calledMethods[-1].args[1]
            callback() # sok.recv
            callback() # sok.recv
            callback() # addProcess
            self.assertEqualsWS(ONE_RECORD, observer.calledMethods[1].kwargs['data'])

    def _prepareDownloader(self, host, port, period=1, handleGenerator=None, proxyServer=None):
        handleGenerator = handleGenerator or (x for x in 'X')
        self._reactor = CallTrace("reactor")
        timerCounter = count(0)
        self._reactor.methods['addTimer'] = lambda *args, **kwargs: 'timerObject%s' % next(timerCounter)
        self._downloader = PeriodicDownload(self._reactor, host, port, schedule=Schedule(period=period), prio=0, err=StringIO())
        self._observer = CallTrace("observer", methods={'handle': lambda data: handleGenerator})
        if proxyServer:
            self._observer.returnValues["buildRequest"] = dict(request=b"GET /path?argument=value HTTP/1.0\r\n\r\n", host=host, port=port, proxyServer=proxyServer)
        else:
            self._observer.returnValues["buildRequest"] = b"GET /path?argument=value HTTP/1.0\r\n\r\n"
        self._downloader.addObserver(self._observer)
        self._downloader.observer_init()
        self.assertEqual(period, self._reactor.calledMethods[0].args[0])
        return self._downloader, self._observer, self._reactor

    def doConnect(self):
        callback = self._reactor.calledMethods[0].args[1]
        callback() # startProcess -> tryConnect
        callback = self._reactor.calledMethods[1].args[1]
        return callback # _processOne.next

    def assertReactorStateClean(self, reactor):
        names = [m.name for m in reactor.calledMethods]
        for what in ['Writer', 'Reader', 'Process']:
            self.assertEqual(
                len([n for n in names if n == 'add%s' % what]),
                len([n for n in names if n == 'remove%s' % what]),
                'Expected same amount of add and remove for %s' % what)


HTTP_SEPARATOR = 2 * CRLF
STATUSLINE = """HTTP/1.0 200 OK""" + HTTP_SEPARATOR
STATUSLINE_ALTERNATIVE = """HTTP/1.1 200 ok""" + HTTP_SEPARATOR
DROP_CONNECTION = object()

BODY = """<aap:noot xmlns:aap="mies">%s</aap:noot>"""
EMBEDDED_RECORD = '<record>ignored</record>'
ONE_RECORD = BODY % EMBEDDED_RECORD
TWO_RECORDS = BODY % EMBEDDED_RECORD * 2
RESPONSE_ONE_RECORD = STATUSLINE + ONE_RECORD
RESPONSE_TWO_RECORDS = STATUSLINE + TWO_RECORDS

def _dunderFile(): pass
fileDict = {
    '__file__': _dunderFile.__code__.co_filename,
    'periodicdownload.py': PeriodicDownload.__init__.__code__.co_filename,
}

def proxyServer(port, request):
    def server(httpd):
        httpd.serve_forever()
    class Proxy(BaseHTTPRequestHandler):
        def log_message(*args, **kwargs):
            pass

        def do_CONNECT(self):
            request.append({'command': self.command, 'path': self.path, 'headers': self.headers})
            self.send_response(200, "Connection established")
            self.end_headers()
            origRequest = self.connection.recv(4096)
            path = "http://" + self.path + origRequest.decode().split()[1]
            self.wfile.write(b"HTTP/1.0 200 OK\r\n\r\n")
            with urlopen(path) as strm:
                self.wfile.write(strm.read())
            self.wfile.flush()
            self.connection.close()

    httpd = TCPServer(("", port), Proxy)
    thread=Thread(None, lambda: server(httpd))
    thread.daemon = True
    thread.start()
