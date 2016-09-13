## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2013-2014, 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2014 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2016 SURFmarket https://surf.nl
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

from seecr.test import SeecrTestCase,CallTrace
from weightless.core import compose
from meresco.core import Observable

from meresco.components.http import BasicHttpHandler

class BasicHttpHandlerTest(SeecrTestCase):
    def test404(self):
        handler = BasicHttpHandler()
        observer = CallTrace('HttpComponent', emptyGeneratorMethods=['handleRequest'])
        observable = Observable()
        observable.addObserver(handler)
        handler.addObserver(observer)

        response = ''.join(compose(observable.all.handleRequest(RequestURI="/")))

        self.assertEquals('HTTP/1.0 404 Not Found\r\nContent-Type: text/html; charset=utf-8\r\n\r\n<html><body>404 Not Found</body></html>', response)
        self.assertEquals(['handleRequest'], observer.calledMethodNames())

    def testOk(self):
        handler = BasicHttpHandler()
        observer = CallTrace('HttpComponent')
        observer.returnValues['handleRequest'] = (f for f in ['HTTP/1.0 200 OK\r\n\r\n', 'Body'])
        observable = Observable()
        observable.addObserver(handler)
        handler.addObserver(observer)

        response = ''.join(compose(observable.all.handleRequest(RequestURI="/")))

        self.assertEquals('HTTP/1.0 200 OK\r\n\r\nBody', response)
        self.assertEquals(['handleRequest'], observer.calledMethodNames())

    def testAlternativeMethod(self):
        handler = BasicHttpHandler(notFoundMethod=lambda path, **kwargs: 'HTTP/1.0 404\r\n\r\n%s' % path)
        observer = CallTrace('HttpComponent', emptyGeneratorMethods=['handleRequest'])
        observable = Observable()
        observable.addObserver(handler)
        handler.addObserver(observer)

        response = ''.join(compose(observable.all.handleRequest(RequestURI="/", path='/')))

        self.assertEquals('HTTP/1.0 404\r\n\r\n/', response)
        self.assertEquals(['handleRequest'], observer.calledMethodNames())

    def testRedirect(self):
        handler = BasicHttpHandler.createWithRedirect('http://example.org/here')
        observer = CallTrace('HttpComponent', emptyGeneratorMethods=['handleRequest'])
        observable = Observable()
        observable.addObserver(handler)
        handler.addObserver(observer)

        response = ''.join(compose(observable.all.handleRequest(RequestURI="/")))

        self.assertEquals('HTTP/1.0 302 Found\r\nLocation: http://example.org/here\r\n\r\n', response)
        self.assertEquals(['handleRequest'], observer.calledMethodNames())
