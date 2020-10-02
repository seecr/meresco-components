## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from unittest import TestCase
from seecr.test import CallTrace
from io import StringIO
from weightless.core import compose

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

        self.assertEqual(okPlainText + 'text', result)

        logline = output.getvalue()
        beforeTimestamp = logline.split('[',1)[0]
        afterTimestamp = logline.split(']', 1)[-1]
        self.assertEqual('127.0.0.1 - - ', beforeTimestamp)
        self.assertEqual(' "GET /path?key=value HTTP/1.0" 200 ?? "-" "-"\n'
                , afterTimestamp)

        self.assertEqual(['handleRequest'], [m.name for m in observer.calledMethods])
        self.assertEqual([dict(Method='GET', Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', query='key=value', path='/path', Headers={}, otherKwarg='value')], [m.kwargs for m in observer.calledMethods])

    def testLogHttpError(self):
        output = StringIO()
        logger = ApacheLogger(output)
        observer = CallTrace('handler')
        logger.addObserver(observer)

        logger.logHttpError(Method='GET', ResponseCode=503, Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', Headers={}, otherKwarg='value')

        logline = output.getvalue()
        beforeTimestamp = logline.split('[',1)[0]
        afterTimestamp = logline.split(']', 1)[-1]
        self.assertEqual('127.0.0.1 - - ', beforeTimestamp)
        self.assertEqual(' "GET /path?key=value HTTP/1.0" 503 ?? "-" "-"\n'
                , afterTimestamp)

        self.assertEqual(['logHttpError'], [m.name for m in observer.calledMethods])
        self.assertEqual([dict(Method='GET', ResponseCode=503, Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', Headers={}, otherKwarg='value')], [m.kwargs for m in observer.calledMethods])

    def testHandleRequestAsynchronous(self):
        logger = ApacheLogger(StringIO())
        observer = CallTrace('handler')
        observer.returnValues['handleRequest'] = (f for f in [str, okPlainText, 'text', int])
        logger.addObserver(observer)
        
        result = list(compose(logger.handleRequest(Method='GET', Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', query='key=value', path='/path', Headers={}, otherKwarg='value'))) 

        self.assertEqual([str, okPlainText, 'text', int], result)
