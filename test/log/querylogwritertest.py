## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2014, 2016 Stichting Kennisnet http://www.kennisnet.nl
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
from meresco.components.log import QueryLogWriter, HandleRequestLog, LogCollector, LogCollectorScope
from weightless.core import be, asString
from meresco.core import Observable
from meresco.components.http import PathFilter
from meresco.components.http.utils import okPlainText
from decimal import Decimal

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
        self.assertEqual(okPlainText+'result', result)
        result = asString(observable.all.handleRequest(Client=('22.33.44.55', 2345), path='/no'))
        self.assertEqual(okPlainText+'result', result)
        result = asString(observable.all.handleRequest(Client=('33.44.55.66', 3456), path='/yes'))
        self.assertEqual(okPlainText+'result', result)
        self.assertEqual(['log', 'log'], log.calledMethodNames())
        self.assertEqual(['/yes', '/yes'], [m.kwargs['path'] for m in log.calledMethods])

    def testLogAllPaths(self):
        log = CallTrace('log')
        writer = QueryLogWriter(log=log)
        writer.writeLog(defaultCollectedLogWithPath('/sru'))
        writer.writeLog(defaultCollectedLogWithPath('/srv'))
        writer.writeLog(defaultCollectedLogWithPath('/srw.php'))
        self.assertEqual(['log','log', 'log'], log.calledMethodNames())
        self.assertEqual(['/sru', '/srv', '/srw.php'], [m.kwargs['path'] for m in log.calledMethods])

    def testLogAsObservable(self):
        log = CallTrace('log', onlySpecifiedMethods=True, methods={'log': lambda **kwargs: None})
        writer = QueryLogWriter()
        writer.addObserver(log)
        writer.writeLog(defaultCollectedLogWithPath('/sru'))
        self.assertEqual(['log'], log.calledMethodNames())
        self.assertEqual(['/sru'], [m.kwargs['path'] for m in log.calledMethods])

    def testLog(self):
        log = CallTrace('log')
        writer = QueryLogWriter(log=log)
        collectedLog = defaultCollectedLog()
        collectedLog['httpResponse']['size'] = [4096]
        collectedLog['httpResponse']['httpStatus'] = ['200']
        writer.writeLog(collectedLog)
        self.assertEqual(['log'], log.calledMethodNames())
        self.assertEqual(dict(
                timestamp=1257161136.0,
                path='/sru',
                ipAddress='11.22.33.44',
                size=4.0,
                duration=3.0,
                queryArguments='version=1.2',
                numberOfRecords=32,
                status='200'
            ), log.calledMethods[0].kwargs)

    def testLogForArgumentsInsteadOfSruArguments(self):
        log = CallTrace('log')
        writer = QueryLogWriter.forHttpArguments(log=log)
        collectedLog = defaultCollectedLog()
        collectedLog['httpRequest']['arguments'] = [{'verb':'ListRecords', 'metadataPrefix':'rdf'}]
        writer.writeLog(collectedLog)
        self.assertEqual(['log'], log.calledMethodNames())
        self.assertEqual(['metadataPrefix=rdf&verb=ListRecords'], [m.kwargs['queryArguments'] for m in log.calledMethods])

    def testLogForNumberOfRecordsSelection(self):
        log = CallTrace('log')
        writer = QueryLogWriter(log=log, numberOfRecordsSelection=dict(scope='myscope', key='total'))
        collectedLog = defaultCollectedLog()
        collectedLog['myscope'] = {'total': [100]}
        writer.writeLog(collectedLog)
        self.assertEqual(['log'], log.calledMethodNames())
        self.assertEqual([100], [m.kwargs['numberOfRecords'] for m in log.calledMethods])

    def testLogLiveExample(self):
        collectedLog = {
            'httpRequest': {
                'timestamp': [1396596372.708574],
                'Headers': [{}],
                'Client': [('127.0.0.1', 57075)],
                'arguments': [{
                    'query': ['meta.upload.id exact "NICL:oai:mdms.kenict.org:oai:nicl.nl:k163645"'],
                    'operation': ['searchRetrieve'],
                    'version': ['1.2'],
                    'recordPacking': ['xml'],
                    'recordSchema': ['smbAggregatedData']
                }],
                'RequestURI': ['/edurep/sruns?query=meta.upload.id+exact+%22NICL%3Aoai%3Amdms.kenict.org%3Aoai%3Anicl.nl%3Ak163645%22&operation=searchRetrieve&version=1.2&recordPacking=xml&recordSchema=smbAggregatedData'],
                'query': ['query=meta.upload.id+exact+%22NICL%3Aoai%3Amdms.kenict.org%3Aoai%3Anicl.nl%3Ak163645%22&operation=searchRetrieve&version=1.2&recordPacking=xml&recordSchema=smbAggregatedData'],
                'path': ['/edurep/sruns'],
                'Method': ['GET'],
                'HTTPVersion': ['1.0']
            },
            'query-scope': {
                'sub-scope': {
                    'cqlClauses': [2],
                    'sru': {
                        'indexTime': [Decimal('0.000')],
                        'handlingTime': [Decimal('0.004')],
                        'numberOfRecords': [1],
                        'queryTime': [Decimal('0.003')],
                        'arguments': [{
                            'recordSchema': 'smbAggregatedData',
                            'version': '1.2',
                            'recordPacking': 'xml',
                            'maximumRecords': 10,
                            'startRecord': 1,
                            'query': 'meta.upload.id exact "NICL:oai:mdms.kenict.org:oai:nicl.nl:k163645"',
                            'operation': 'searchRetrieve'
                        }]
                    }
                }
            },
            'httpResponse': {
                'duration': [0.004216909408569336],
                'httpStatus': ['200'],
                'size': [1889]
            }
        }
        log = CallTrace('log')
        writer = QueryLogWriter(log=log, scopeNames=('query-scope', 'sub-scope'))
        log2 = CallTrace('log')
        writer2 = QueryLogWriter(log=log2, scopeNames=('query-scope', 'other-scope'))
        writer.writeLog(collectedLog)
        writer2.writeLog(collectedLog)
        self.assertEqual(['log'], log.calledMethodNames())
        self.assertEqual([], log2.calledMethodNames())
        self.assertEqual(['maximumRecords=10&operation=searchRetrieve&query=meta.upload.id+exact+%22NICL%3Aoai%3Amdms.kenict.org%3Aoai%3Anicl.nl%3Ak163645%22&recordPacking=xml&recordSchema=smbAggregatedData&startRecord=1&version=1.2'], [m.kwargs['queryArguments'] for m in log.calledMethods])

    def testAdditionalArguments(self):
        log = CallTrace('log')
        writer = QueryLogWriter(log=log)
        observer = CallTrace('additional', returnValues={'determineQueryArguments': dict(key='value')})
        writer.addObserver(observer)
        writer.writeLog(defaultCollectedLog())
        self.assertEqual(['log'], log.calledMethodNames())
        self.assertEqual(['key=value'], [m.kwargs['queryArguments'] for m in log.calledMethods])
        self.assertEqual(['determineQueryArguments'], observer.calledMethodNames())
        self.assertEqual(dict(
                collectedLog=defaultCollectedLog(),
                scopeNames=(),
                currentArgs={'version': '1.2'},
            ), observer.calledMethods[0].kwargs)


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