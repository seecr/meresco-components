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
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from socket import socket
from seecr.test import SeecrTestCase, CallTrace
from weightless.io import Reactor
from weightless.core import compose

from meresco.components.http import ObservableHttpServer
from meresco.components.http.utils import CRLF
from random import randint

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
        with ObservableHttpServer(CallTrace('Reactor'), 1024) as s:
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

        with ObservableHttpServer(reactor, 1024, maxConnections=5) as s:
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

        with ObservableHttpServer(reactor, 1024, maxConnections=5) as s:
            s.startServer()

            acceptor = s._server._acceptor
            httphandler = acceptor._sinkFactory('sok')
            errorHandler = httphandler._errorHandler
            self.assertTrue(errorHandler == s._error)

    def testSetMaximumConnections(self):
        reactor = CallTrace('Reactor')

        with ObservableHttpServer(reactor, 2048, maxConnections=5) as s:
            s.startServer()

            httpserver = s._server
            self.assertEqual(5, httpserver._maxConnections)
            s.setMaxConnections(6)
            acceptor = s._server
            self.assertEqual(6, httpserver._maxConnections)
            self.assertEqual(6, httpserver._acceptor._sinkFactory('a sink')._maxConnections)

    def testCompressResponseFlag(self):
        reactor = CallTrace('Reactor')

        with ObservableHttpServer(reactor, 0, compressResponse=True) as s:
            s.startServer()
            httpserver = s._server
            self.assertEqual(True, httpserver._compressResponse)

        with ObservableHttpServer(reactor, 0) as s:
            s.startServer()
            httpserver = s._server
            self.assertEqual(False, httpserver._compressResponse)

    def testServerWithPrio(self):
        prios = []
        class MyServer(object):
            def handleRequest(self, *args, **kwargs):
                yield 'HALLO'
        class MyReactor(Reactor):
            def addReader(self, *args, **kwargs):
                prios.append(('read', kwargs['prio']))
                return Reactor.addReader(self, *args, **kwargs)
            def addWriter(self, *args, **kwargs):
                prios.append(('write', kwargs['prio']))
                return Reactor.addWriter(self, *args, **kwargs)
        reactor = MyReactor()
        with ObservableHttpServer(reactor, 2000, prio=3) as s:
            s.addObserver(MyServer())
            s.observer_init()

            with socket() as sok:
                sok.connect(('localhost', 2000))
                sok.send(b'GET / HTTP/1.0\r\n\r\n')
                reactor.step()
                reactor.step()
                self.assertEqual([('read', 3)], prios)
                reactor.step().step()
                self.assertEqual([('read', 3), ('read', 3)], prios)
                reactor.step()
                reactor.step()
                self.assertEqual([('read', 3), ('read', 3), ('write', 3)], prios)
                # one more step to let the connection finalize and all objects reclaimed and avoid garbage
                reactor.step()

    def testServerBindAddress(self):
        reactor = CallTrace()
        port = randint(2**10, 2**16)
        with ObservableHttpServer(reactor, port, bindAddress='127.0.0.1') as server:
            server.startServer()
            self.assertEqual(('127.0.0.1', port), server._server._acceptor._sok.getsockname())
