## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from seecr.test import SeecrTestCase, CallTrace
from seecr.test.portnumbergenerator import PortNumberGenerator

from weightless.core import compose

from meresco.components.http import ObservableHttpServer
from meresco.components.http.observablehttpserver import _convertToStrings
from meresco.components.http.utils import CRLF


class ObservableHttpServerTest(SeecrTestCase):
    def testSimpleHandleRequest(self):
        observer = CallTrace('Observer', methods={'handleRequest': lambda *a, **kw: (x for x in [])})
        s = ObservableHttpServer(CallTrace('Reactor'), 1024)
        s.addObserver(observer)

        list(compose(s.handleRequest(RequestURI='http://localhost')))
        self.assertEqual(1, len(observer.calledMethods))
        method = observer.calledMethods[0]
        self.assertEqual('handleRequest', method.name)
        self.assertEqual(0, len(method.args))
        self.assertEqual(7, len(method.kwargs))

    def testHandleRequest(self):
        observer = CallTrace('Observer', methods={'handleRequest': lambda *a, **kw: (x for x in [])})
        s = ObservableHttpServer(CallTrace('Reactor'), 1024)
        s.addObserver(observer)

        list(compose(s.handleRequest(RequestURI='http://localhost/path?key=value&emptykey#fragment')))
        self.assertEqual(1, len(observer.calledMethods))
        method = observer.calledMethods[0]
        self.assertEqual('handleRequest', method.name)
        self.assertEqual(0, len(method.args))
        self.assertEqual(7, len(method.kwargs))
        self.assertTrue('arguments' in method.kwargs, method.kwargs)
        arguments = method.kwargs['arguments']
        self.assertEqual(2, len(arguments))
        self.assertEqual(['emptykey', 'key'], sorted(arguments.keys()))
        self.assertEqual(['value'], arguments['key'])
        self.assertEqual([''], arguments['emptykey'])

    def testMaxConnectionsErrorHandling(self):
        observer = CallTrace('Observer', methods={'handleRequest': lambda *a, **kw: (x for x in [])})
        reactor = CallTrace('Reactor')

        s = ObservableHttpServer(reactor, 1024, maxConnections=5)
        s.addObserver(observer)
        result = ''.join(s._error(ResponseCode=503, something='bicycle'))

        self.assertEqual(1, len(observer.calledMethods))
        self.assertEqual('logHttpError', observer.calledMethods[0].name)
        self.assertEqual({'ResponseCode': 503, 'something': 'bicycle'}, observer.calledMethods[0].kwargs)
        header, body = result.split(CRLF * 2)
        self.assertTrue(header.startswith('HTTP/1.0 503'), header)
        self.assertTrue('Service Unavailable' in body, body)

    def testErrorHandlerRegisteredOnWeightlessHttpServer(self):
        reactor = CallTrace('Reactor')

        s = ObservableHttpServer(reactor, 1024, maxConnections=5)
        s.startServer()
        try:
            acceptor = s._httpserver._acceptor
            httphandler = acceptor._sinkFactory('sok')
            errorHandler = httphandler._errorHandler
            self.assertTrue(errorHandler == s._error)
        finally:
            s.shutdown()

    def testSetMaximumConnections(self):
        reactor = CallTrace('Reactor')

        s = ObservableHttpServer(reactor, 2048, maxConnections=5)
        s.startServer()
        try:
            httpserver = s._httpserver
            self.assertEqual(5, httpserver._maxConnections)
            s.setMaxConnections(6)
            self.assertEqual(6, httpserver._maxConnections)
            self.assertEqual(6, httpserver._acceptor._sinkFactory('a sink')._maxConnections)
        finally:
            s.shutdown()

    def testCompressResponseFlag(self):
        reactor = CallTrace('Reactor')

        s = ObservableHttpServer(reactor, 0)
        s.startServer()
        try:
            httpserver = s._httpserver
            self.assertEqual(True, httpserver._compressResponse)
        finally:
            s.shutdown()

        s = ObservableHttpServer(reactor, 0, compressResponse=True)
        s.startServer()
        try:
            httpserver = s._httpserver
            self.assertEqual(True, httpserver._compressResponse)
        finally:
            s.shutdown()

        s = ObservableHttpServer(reactor, 0, compressResponse=False)
        s.startServer()
        try:
            httpserver = s._httpserver
            self.assertEqual(False, httpserver._compressResponse)
        finally:
            s.shutdown()

    def testServerWithPrio(self):
        reactor = CallTrace('reactor')
        s = ObservableHttpServer(reactor, 2000, prio=3)
        s.observer_init()
        try:
            self.assertEqual(['addReader'], reactor.calledMethodNames())
            self.assertEqual(3, reactor.calledMethods[0].kwargs['prio'])
        finally:
            s.shutdown()

    def testServerBindAddress(self):
        reactor = CallTrace()
        port = next(PortNumberGenerator)
        server = ObservableHttpServer(reactor, port, bindAddress='127.0.0.1')
        server.startServer()
        try:
            self.assertEqual(('127.0.0.1', port), server._httpserver._acceptor._sok.getsockname())
        finally:
            server.shutdown()

    def testConvertToString(self):
        self.assertEqual(
                {'scheme': '', 'netloc': '', 'path': '/path', 'query': 'query', 'fragments': '', 'arguments': {'query': ['']}, 'RequestURI': '/path?query', 'port': 6060, 'Method': 'GET', 'HTTPVersion': '1.1', 'Body': '', 'Headers': {'User-Agent': 'Wget/1.20.1 (linux-gnu)', 'Accept': '*/*', 'Accept-Encoding': 'identity', 'Host': 'localhost:6060', 'Connection': 'Keep-Alive'}, 'Client': ('127.0.0.1', 48506)}, 
                _convertToStrings({'scheme': b'', 'netloc': b'', 'path': b'/path', 'query': b'query', 'fragments': b'', 'arguments': {b'query': [b'']}, 'RequestURI': b'/path?query', 'port': 6060, 'Method': b'GET', 'HTTPVersion': b'1.1', 'Body': b'', 'Headers': {b'User-Agent': b'Wget/1.20.1 (linux-gnu)', b'Accept': b'*/*', b'Accept-Encoding': b'identity', b'Host': b'localhost:6060', b'Connection': b'Keep-Alive'}, 'Client': ('127.0.0.1', 48506)}))
