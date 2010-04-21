## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from unittest import TestCase
from cq2utils import CallTrace
from StringIO import StringIO
from weightless import compose

from meresco.components.http import ApacheLogger
from meresco.components.http.utils import okPlainText

class ApacheLoggerTest(TestCase):
    def testLogHandleRequest(self):
        output = StringIO()
        logger = ApacheLogger(output)
        observer = CallTrace('handler')
        observer.returnValues['handleRequest'] = (f for f in [okPlainText, 'text'])
        logger.addObserver(observer)
        
        result = ''.join(compose(logger.handleRequest(Method='GET', Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', query='key=value', path='/path', Headers={}, otherKwarg='value'))) 

        self.assertEquals(okPlainText + 'text', result)

        logline = output.getvalue()
        beforeTimestamp = logline.split('[',1)[0]
        afterTimestamp = logline.split(']', 1)[-1]
        self.assertEquals('127.0.0.1 - - ', beforeTimestamp)
        self.assertEquals(' "GET /path?key=value HTTP/1.0" 200 ?? "-" "-"\n'
                , afterTimestamp)

        self.assertEquals(['handleRequest'], [m.name for m in observer.calledMethods])
        self.assertEquals([dict(Method='GET', Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', query='key=value', path='/path', Headers={}, otherKwarg='value')], [m.kwargs for m in observer.calledMethods])

    def testLogHttpError(self):
        output = StringIO()
        logger = ApacheLogger(output)
        observer = CallTrace('handler')
        logger.addObserver(observer)

        logger.logHttpError(Method='GET', ResponseCode=503, Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', Headers={}, otherKwarg='value')

        logline = output.getvalue()
        beforeTimestamp = logline.split('[',1)[0]
        afterTimestamp = logline.split(']', 1)[-1]
        self.assertEquals('127.0.0.1 - - ', beforeTimestamp)
        self.assertEquals(' "GET /path?key=value HTTP/1.0" 503 ?? "-" "-"\n'
                , afterTimestamp)

        self.assertEquals(['logHttpError'], [m.name for m in observer.calledMethods])
        self.assertEquals([dict(Method='GET', ResponseCode=503, Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', Headers={}, otherKwarg='value')], [m.kwargs for m in observer.calledMethods])

