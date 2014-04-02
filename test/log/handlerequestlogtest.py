## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2014 Stichting Kennisnet http://www.kennisnet.nl
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
from meresco.components.http.utils import okPlainText
from weightless.core import be, Yield, consume
from meresco.core import Observable
from meresco.components.log import LogCollector, HandleRequestLog, ApacheLogWriter
from StringIO import StringIO
from time import time
from weightless.core.utils import asList

class HandleRequestLogTest(SeecrTestCase):

    def testApacheLog(self):
        requestHandler = CallTrace('handler', ignoredAttributes=['writeLog', 'do_unknown'])
        requestHandler.returnValues['handleRequest'] = (f for f in [Yield, okPlainText, 'te', callable, 'xt'])
        stream = StringIO()
        handleRequestLog = HandleRequestLog()
        handleRequestLog._time = lambda: 1395409143.0

        observable = be((Observable(),
            (LogCollector(),
                (handleRequestLog,
                    (requestHandler,)
                ),
                (ApacheLogWriter(stream),),
            )
        ))

        result = asList(observable.all.handleRequest(Method='GET', Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', query='key=value', path='/path', Headers={'Referer': 'http://meresco.org', 'User-Agent': 'Meresco-Components Test'}, otherKwarg='value'))

        self.assertEquals([Yield, okPlainText, 'te', callable, 'xt'], result)
        self.assertEquals(['handleRequest'], requestHandler.calledMethodNames())
        logline = stream.getvalue()
        self.assertEquals('127.0.0.1 - - [21/Mar/2014:13:39:03 +0000] "GET /path?key=value HTTP/1.0" 200 64 "http://meresco.org" "Meresco-Components Test"\n', logline)

    def testLogHttpError(self):
        requestHandler = CallTrace('handler', ignoredAttributes=['writeLog', 'do_unknown'])
        stream = StringIO()
        handleRequestLog = HandleRequestLog()
        handleRequestLog._time = lambda: 1395409143.0

        observable = be((Observable(),
            (LogCollector(),
                (handleRequestLog,
                    (requestHandler,),
                ),
                (ApacheLogWriter(stream),),
            )
        ))

        # called by ObservableHttpServer
        observable.do.logHttpError(Method='GET', ResponseCode=503, Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', Headers={}, otherKwarg='value')

        logline = stream.getvalue()
        self.assertEquals('127.0.0.1 - - [21/Mar/2014:13:39:03 +0000] "GET /path?key=value HTTP/1.0" 503 - "-" "-"\n', logline)
        self.assertEquals(['logHttpError'], requestHandler.calledMethodNames())
        self.assertEquals(dict(Method='GET', ResponseCode=503, Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', Headers={}, otherKwarg='value'), requestHandler.calledMethods[0].kwargs)

    def testDefaultTimeIsNow(self):
        __callstack_var_logCollector__ = dict()
        consume(HandleRequestLog().handleRequest(Method='GET', ResponseCode=503, Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', Headers={}, otherKwarg='value'))
        self.assertAlmostEqual(time(), __callstack_var_logCollector__['httpRequest']['timestamp'][0], places=1)


    def testPostBody(self):
        __callstack_var_logCollector__ = dict()
        consume(HandleRequestLog().handleRequest(Method='POST', Client=('127.0.0.1', 1234), RequestURI='http://example.org/path?key=value', Headers={}, otherKwarg='value', Body='short'))

        self.assertEquals(5, __callstack_var_logCollector__['httpRequest']['bodySize'][0])


