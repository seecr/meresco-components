# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2006-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2006-2012 Stichting Kennisnet http://www.kennisnet.nl
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

from seecr.test import SeecrTestCase, CallTrace

from os.path import isfile, isdir, join
from os import listdir

from meresco.components.log import QueryLog, QueryLogHelper, QueryLogHelperForSru, DirectoryLog, QueryLogHelperForExecuteCQL
from meresco.components.log.directorylog import NR_OF_FILES_KEPT
from meresco.components.facetindex import Response

from meresco.core import Observable
from weightless.core import compose, be
from meresco.components.sru import SruHandler, SruParser

from weightless.core import compose

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

        self.assertEquals('123', result)
        self.assertEquals(['handleRequest'], [m.name for m in observer.calledMethods])
        self.assertEquals([dict(Client=('127.0.0.1', 47785), path='/path/sru', otherArg='value')], [m.kwargs for m in observer.calledMethods])

        self.assertTrue(isfile(join(self.tempdir, '2009-11-02-query.log')))
        self.assertEquals('2009-11-02T11:25:37Z 127.0.0.1 0.0K 1.000s - /path/sru \n', open(join(self.tempdir, '2009-11-02-query.log')).read())

    def testAddToLogfile(self):
        f = open(join(self.tempdir, '2009-11-02-query.log'), 'w')
        f.write('line0\n')
        f.close()
        observer = CallTrace('observer')
        observer.returnValues['handleRequest'] = (line for line in ['1','2','3'])
        self.queryLog.addObserver(observer)
        ''.join(compose(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/path/sru', otherArg='value')))

        self.assertEquals(2, len(open(join(self.tempdir, '2009-11-02-query.log')).readlines()))

    def testLogCanReturnCallables(self):
        observer= CallTrace('observer')
        observer.returnValues['handleRequest'] = (f for f in ['1', lambda: None,'3'])
        self.queryLog.addObserver(observer)
        list(compose(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/path/sru', otherArg='value')))

        self.assertEquals(1, len(open(join(self.tempdir, '2009-11-02-query.log')).readlines()))
        
    def testNewDayNewLogfile(self):
        observer = CallTrace('observer')
        observer.returnValues['handleRequest'] = (line for line in ['1','2','3'])
        self.queryLog.addObserver(observer)
        ''.join(compose(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/path/sru', otherArg='value')))
        self._timeNow += 24 * 60 *60
        observer.returnValues['handleRequest'] = (line for line in ['1','2','3'])
        ''.join(compose(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/path/sru', otherArg='value')))

        self.assertEquals(['2009-11-02-query.log', '2009-11-03-query.log'], sorted(listdir(self.tempdir)))

    def testIncludedPathsOnly(self):
        observer = CallTrace('observer')
        observer.returnValues['handleRequest'] = (line for line in ['1','2','3'])
        self.queryLog.addObserver(observer)
        result = ''.join(compose(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/not/included', otherArg='value')))

        self.assertEquals('123', result)
        self.assertEquals(0, len(listdir(self.tempdir)))


    def testLoggedPathsIsStartOfAcceptedPath(self):
        observer = CallTrace('observer')
        observer.returnValues['handleRequest'] = (line for line in ['1','2','3'])
        self.queryLog.addObserver(observer)
        ''.join(compose(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/path/sru/extended/path', otherArg='value')))
        self.assertEquals(1, len(listdir(self.tempdir)))
        
    def testLogDirCreated(self):
        logDir = join(self.tempdir, 'amihere')
        self.assertFalse(isdir(logDir))
        
        queryLog = QueryLog(log=DirectoryLog(logDir), loggedPaths=None)
        self.assertTrue(isdir(logDir))

    def testSetExtension(self):
        queryLog = QueryLog(log=DirectoryLog(self.tempdir, extension='-q.ext'), loggedPaths=['/'])
        queryLog._time = self.queryLog._time
        observer = CallTrace('observer')
        observer.returnValues['handleRequest'] = (line for line in ['1','2','3'])
        queryLog.addObserver(observer)
        ''.join(queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/path/sru/extended/path', otherArg='value'))
        self.assertEquals(1, len(listdir(self.tempdir)))
        self.assertEquals('2009-11-02T11:25:37Z 127.0.0.1 0.0K 1.000s - /path/sru/extended/path \n', open(join(self.tempdir, '2009-11-02-q.ext')).read())

    def testLogQueryParameters(self):
        class HandleRequestObserver(Observable):
            def handleRequest(self, **kwargs):
                self.ctx.queryLogValues['queryArguments'].update({'a':'A', 'b':'B', 'c':'C', 'd':['D','DD']})
                yield 'result'
        self.queryLog.addObserver(HandleRequestObserver())
        result = ''.join(compose(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path='/path/sru', otherArg='value')))
        self.assertEquals('result', result)
        self.assertEquals('2009-11-02T11:25:37Z 127.0.0.1 0.0K 1.000s - /path/sru a=A&b=B&c=C&d=D&d=DD\n', open(join(self.tempdir, '2009-11-02-query.log')).read())

    def testQueryLogHelperForSru(self):
        __callstack_var_queryLogValues__ = {'queryArguments':{}}
        helper = QueryLogHelperForSru()
        observer = CallTrace('observer')
        helper.addObserver(observer)
        def searchRetrieve(**kwargs):
            yield 'result'
        observer.methods['searchRetrieve'] = searchRetrieve
        list(compose(helper.searchRetrieve(query=['query'], x_term_drilldown='drilldown', sortBy='field', sortDescending=False, **{'x-term-drilldown':'drilldown', 'under_score':'value', 'sortKeys':'field,,0'})))
        self.assertEquals({'query': ['query'], 'x-term-drilldown': 'drilldown', 'under_score': 'value', 'sortKeys':'field,,0'}, __callstack_var_queryLogValues__['queryArguments'])
        
    def testQueryLogHelper(self):
        __callstack_var_queryLogValues__ = {'queryArguments':{}}
        helper = QueryLogHelper()
        observer = CallTrace('observer')
        helper.addObserver(observer)
        def handleRequest(**kwargs):
            yield 'result'
        observer.methods['handleRequest'] = handleRequest
        result = list(compose(helper.handleRequest(arguments={'key':['value'], 'key2':['value1', 'value2']}, path='path')))
        self.assertEquals(['result'], result)
        self.assertEquals({'key':['value'], 'key2':['value1', 'value2']}, __callstack_var_queryLogValues__['queryArguments'])
        self.assertEquals([{'arguments': {'key':['value'], 'key2':['value1', 'value2']}, 'path':'path'}], [m.kwargs for m in observer.calledMethods])

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
        self.assertEquals('2009-11-02T11:25:37Z 11.22.33.44 0.7K 1.000s 3201hits /path/sru maximumRecords=0&operation=searchRetrieve&query=field%3Dvalue&recordPacking=xml&recordSchema=dc&startRecord=1&version=1.2\n', open(join(self.tempdir, '2009-11-02-query.log')).read())

    def testRemoveOldLogs(self):
        for filename in ("%03d" % r for r in range(NR_OF_FILES_KEPT)):
            open(join(self.tempdir, filename), 'w').close()
        
        filesBefore = listdir(self.tempdir)
        "".join(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path="/path/sru"))
        filesAfter = listdir(self.tempdir)
        self.assertFalse('000' in filesAfter)
        self.assertEquals(len(filesAfter), len(filesBefore))
        
        filesBefore = listdir(self.tempdir)
        self._timeNow += 3600*24
        "".join(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path="/path/sru"))
        filesAfter = listdir(self.tempdir)
        self.assertFalse('001' in filesAfter)
        self.assertEquals(len(filesAfter), len(filesBefore))

        open(join(self.tempdir, '015'), 'w').close()
        open(join(self.tempdir, '016'), 'w').close()
        self._timeNow += 3600*24
        "".join(self.queryLog.handleRequest(Client=('127.0.0.1', 47785), path="/path/sru"))
        self.assertEquals(NR_OF_FILES_KEPT, len(listdir(self.tempdir)))
        

