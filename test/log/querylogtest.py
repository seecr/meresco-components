# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2006-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2006-2012, 2014 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from os.path import isfile, isdir, join
from os import listdir

from meresco.components.log import QueryLog, QueryLogHelper, QueryLogHelperForSru, DirectoryLog, QueryLogHelperForExecuteCQL
from meresco.components.log.directorylog import NR_OF_FILES_KEPT
from testhelpers import Response

from meresco.core import Observable
from weightless.core import compose, be
from meresco.components.sru import SruHandler, SruParser

class QueryLogTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self._timeNow = 1257161136.0 # 2009-11-02 11:30:00
        def time():
            self._timeNow += 1.0
            return self._timeNow
        directoryLog = DirectoryLog(self.tempdir)
        self.queryLog = QueryLog(log=directoryLog, loggedPaths=['/path/sru', '/path/srw'])
        self.queryLog._time = time

    def testLogging(self):
        observer = CallTrace('observer')
        observer.returnValues['handleRequest'] = (line for line in ['1','2','3'])
        self.queryLog.addObserver(observer)
        result = ''.join(compose(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/path/sru', otherArg='value')))

        self.assertEqual('123', result)
        self.assertEqual(['handleRequest'], [m.name for m in observer.calledMethods])
        self.assertEqual([dict(Client=('127.0.0.1', 47785), path='/path/sru', otherArg='value')], [m.kwargs for m in observer.calledMethods])

        self.assertTrue(isfile(join(self.tempdir, '2009-11-02-query.log')))
        self.assertEqual('2009-11-02T11:25:37Z 127.0.0.1 0.0K 1.000s - /path/sru \n', open(join(self.tempdir, '2009-11-02-query.log')).read())

    def testLogCanReturnCallables(self):
        observer= CallTrace('observer')
        observer.returnValues['handleRequest'] = (f for f in ['1', lambda: None,'3'])
        self.queryLog.addObserver(observer)
        list(compose(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/path/sru', otherArg='value')))

        self.assertEqual(1, len(open(join(self.tempdir, '2009-11-02-query.log')).readlines()))

    def testIncludedPathsOnly(self):
        observer = CallTrace('observer')
        observer.returnValues['handleRequest'] = (line for line in ['1','2','3'])
        self.queryLog.addObserver(observer)
        result = ''.join(compose(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/not/included', otherArg='value')))

        self.assertEqual('123', result)
        self.assertEqual(0, len(listdir(self.tempdir)))


    def testLoggedPathsIsStartOfAcceptedPath(self):
        observer = CallTrace('observer')
        observer.returnValues['handleRequest'] = (line for line in ['1','2','3'])
        self.queryLog.addObserver(observer)
        ''.join(compose(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/path/sru/extended/path', otherArg='value')))
        self.assertEqual(1, len(listdir(self.tempdir)))

    def testLogQueryParameters(self):
        class HandleRequestObserver(Observable):
            def handleRequest(self, **kwargs):
                self.ctx.queryLogValues['queryArguments'].update({'a':'A', 'b':'B', 'c':'C', 'd':['D','DD']})
                yield 'result'
        self.queryLog.addObserver(HandleRequestObserver())
        result = ''.join(compose(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/path/sru', otherArg='value')))
        self.assertEqual('result', result)
        self.assertEqual('2009-11-02T11:25:37Z 127.0.0.1 0.0K 1.000s - /path/sru a=A&b=B&c=C&d=D&d=DD\n', open(join(self.tempdir, '2009-11-02-query.log')).read())

    def testQueryLogHelperForSru(self):
        __callstack_var_queryLogValues__ = {'queryArguments':{}}
        helper = QueryLogHelperForSru()
        observer = CallTrace('observer')
        helper.addObserver(observer)
        def searchRetrieve(**kwargs):
            yield 'result'
        observer.methods['searchRetrieve'] = searchRetrieve
        list(compose(helper.searchRetrieve(query=['query'], sortKeys=[dict(sortBy='field', sortDescending=False)], sruArguments={'x-term-drilldown':'drilldown', 'under_score':'value', 'sortKeys':'field,,0', 'query': ['query']})))
        self.assertEqual({'query': ['query'], 'x-term-drilldown': 'drilldown', 'under_score': 'value', 'sortKeys':'field,,0'}, __callstack_var_queryLogValues__['queryArguments'])

    def testQueryLogHelper(self):
        __callstack_var_queryLogValues__ = {'queryArguments':{}}
        helper = QueryLogHelper()
        observer = CallTrace('observer')
        helper.addObserver(observer)
        def handleRequest(**kwargs):
            yield 'result'
        observer.methods['handleRequest'] = handleRequest
        result = list(compose(helper.handleRequest(arguments={'key':['value'], 'key2':['value1', 'value2']}, path='path')))
        self.assertEqual(['result'], result)
        self.assertEqual({'key':['value'], 'key2':['value1', 'value2']}, __callstack_var_queryLogValues__['queryArguments'])
        self.assertEqual([{'arguments': {'key':['value'], 'key2':['value1', 'value2']}, 'path':'path'}], [m.kwargs for m in observer.calledMethods])

    def testAllQueryHelpersForSRU(self):
        index = CallTrace('index')
        def executeQuery(**kwargs):
            raise StopIteration(Response(total=3201, hits=[]))
            yield
        index.methods['executeQuery'] = executeQuery
        index.ignoredAttributes.extend(['echoedExtraRequestData', 'extraResponseData', 'all_unknown'])
        server = be((Observable(),
            (self.queryLog,
                (SruParser(),
                    (QueryLogHelperForSru(),
                        (SruHandler(extraRecordDataNewStyle=True),
                            (QueryLogHelperForExecuteCQL(),
                                (index,)
                            )
                        )
                    )
                )
            ),
        ))

        ''.join(compose(server.all.handleRequest(
                path='/path/sru',
                Client=('11.22.33.44', 8080),
                arguments={
                    'operation': ['searchRetrieve'],
                    'version': ['1.2'],
                    'maximumRecords': ['0'],
                    'query': ['field=value'],
                    },
            )))
        self.assertEqual('2009-11-02T11:25:37Z 11.22.33.44 0.7K 1.000s 3201hits /path/sru maximumRecords=0&operation=searchRetrieve&query=field%3Dvalue&recordPacking=xml&recordSchema=dc&startRecord=1&version=1.2\n', open(join(self.tempdir, '2009-11-02-query.log')).read())

