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
from weightless.core import be, asString
from meresco.components.http.utils import okXml
from meresco.components.log import QueryLogWriter, DirectoryLog, HandleRequestLog, LogCollector
from meresco.core import Observable
from os.path import isfile, join

class SruLogTest(SeecrTestCase):

    def testEmptyQuery(self):
        requestHandler = CallTrace('handler', ignoredAttributes=['writeLog', 'do_unknown'])
        requestHandler.returnValues['handleRequest'] = (f for f in [okXml, '<sru>', '</sru>'])
        queryLogWriter = QueryLogWriter(DirectoryLog(self.tempdir))
        handleRequestLog = HandleRequestLog()
        self._timeNow = 1257161136.0 # 2009-11-02 11:30:00
        def time():
            self._timeNow += 1.0
            return self._timeNow
        handleRequestLog._time = time

        observable = be((Observable(),
            (LogCollector(),
                (handleRequestLog,
                    (requestHandler,)
                ),
                (queryLogWriter,),
            )
        ))

        result = asString(observable.all.handleRequest(Method='GET', Client=('127.0.0.1', 1234), arguments={}, path='/path/sru', otherKwarg='value'))

        self.assertEquals(okXml+'<sru></sru>', result)
        self.assertTrue(isfile(join(self.tempdir, '2009-11-02-query.log')))
        self.assertEquals('2009-11-02T11:25:37Z 127.0.0.1 0.1K 1.000s - /path/sru \n', open(join(self.tempdir, '2009-11-02-query.log')).read())

