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
from meresco.components.log import QueryLogWriter, HandleRequestLog, LogCollector, LogCollectorScope
from weightless.core import be, asString
from meresco.core import Observable
from meresco.components.http import PathFilter
from meresco.components.http.utils import okPlainText

class QueryLogWriterTest(SeecrTestCase):

    def testLoggedPathsNewStyle(self):
        log = CallTrace('log')
        def handleRequest(**kwargs):
            yield okPlainText
            yield 'result'
        index = CallTrace('index', methods={'handleRequest':handleRequest})

        observable = be((Observable(),
            (LogCollector(),
                (QueryLogWriter(log=log, scopeNames=('global', 'yesPath')),),
                (LogCollectorScope('global'),
                    (HandleRequestLog(),
                        (PathFilter('/yes'),
                            (LogCollectorScope('yesPath'),
                                (index,),
                            )
                        ),
                        (PathFilter('/no'),
                            (index,),
                        )
                    )
                )
            )
        ))
        result = asString(observable.all.handleRequest(Client=('11.22.33.44', 1234), path='/yes'))
        self.assertEquals(okPlainText+'result', result)
        result = asString(observable.all.handleRequest(Client=('22.33.44.55', 2345), path='/no'))
        self.assertEquals(okPlainText+'result', result)
        result = asString(observable.all.handleRequest(Client=('33.44.55.66', 3456), path='/yes'))
        self.assertEquals(okPlainText+'result', result)
        self.assertEquals(['log', 'log'], log.calledMethodNames())
        self.assertEquals(['/yes', '/yes'], [m.kwargs['path'] for m in log.calledMethods])

    def testLogAllPaths(self):
        log = CallTrace('log')
        writer = QueryLogWriter(log=log)
        writer.writeLog(defaultCollectedLogWithPath('/sru'))
        writer.writeLog(defaultCollectedLogWithPath('/srv'))
        writer.writeLog(defaultCollectedLogWithPath('/srw.php'))
        self.assertEquals(['log','log', 'log'], log.calledMethodNames())
        self.assertEquals(['/sru', '/srv', '/srw.php'], [m.kwargs['path'] for m in log.calledMethods])

    def testLog(self):
        log = CallTrace('log')
        writer = QueryLogWriter(log=log)
        collectedLog = defaultCollectedLog()
        collectedLog['httpResponse']['size'] = [4096]
        writer.writeLog(collectedLog)
        self.assertEquals(['log'], log.calledMethodNames())
        self.assertEquals(dict(
                timestamp=1257161136.0,
                path='/sru',
                ipAddress='11.22.33.44',
                size=4.0,
                duration=3.0,
                queryArguments='version=1.2',
                numberOfRecords=32,
            ), log.calledMethods[0].kwargs)

    def testLogForArgumentsInsteadOfSruArguments(self):
        log = CallTrace('log')
        writer = QueryLogWriter.forHttpArguments(log=log)
        collectedLog = defaultCollectedLog()
        collectedLog['httpRequest']['arguments'] = [{'verb':'ListRecords', 'metadataPrefix':'rdf'}]
        writer.writeLog(collectedLog)
        self.assertEquals(['log'], log.calledMethodNames())
        self.assertEquals(['metadataPrefix=rdf&verb=ListRecords'], [m.kwargs['queryArguments'] for m in log.calledMethods])

def defaultCollectedLog():
    result = dict(
        httpRequest=dict(
            timestamp=[1257161136.0],
            path=['/sru'],
            Client=[('11.22.33.44', 1234)],
        ),
        httpResponse=dict(
            size=[5432],
            duration=[3.0],
        ),
        sru=dict(
            arguments=[{'version':'1.2'}],
            numberOfRecords=[32],
        )
    )
    return result

def defaultCollectedLogWithPath(path):
    result = defaultCollectedLog()
    result['httpRequest']['path'] = [path]
    return result