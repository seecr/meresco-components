# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011-2012 Stichting Kennisnet http://www.kennisnet.nl
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

from os.path import join
from StringIO import StringIO
from urllib2 import urlopen
import sys

import traceback
from lxml.etree import parse, tostring
from xml.sax.saxutils import quoteattr, escape as xmlEscape

from weightless.core import compose

from cqlparser import parseString

from meresco.components.sru.sruparser import MANDATORY_PARAMETER_NOT_SUPPLIED, UNSUPPORTED_PARAMETER, UNSUPPORTED_VERSION, UNSUPPORTED_OPERATION, UNSUPPORTED_PARAMETER_VALUE, QUERY_FEATURE_UNSUPPORTED, SruException
from meresco.components.sru import SruHandler, SruParser
from meresco.components.drilldown import SRUTermDrilldown, DRILLDOWN_HEADER, DRILLDOWN_FOOTER, DEFAULT_MAXIMUM_TERMS
from meresco.components.xml_generic.validate import assertValid
from meresco.components.xml_generic import schemasPath
from meresco.components.facetindex import Response

from seecr.test import SeecrTestCase, CallTrace


SUCCESS = "SUCCESS"

class SruHandlerTest(SeecrTestCase):

    def testEchoedSearchRetrieveRequest(self):
        arguments = {'version':'1.1', 'operation':'searchRetrieve', 'query':'query >= 3', 'recordSchema':'schema', 'recordPacking':'string'}
        component = SruHandler()

        result = "".join(list(component._writeEchoedSearchRetrieveRequest(**arguments)))
        self.assertEqualsWS("""<srw:echoedSearchRetrieveRequest>
    <srw:version>1.1</srw:version>
    <srw:query>query &gt;= 3</srw:query>
    <srw:recordPacking>string</srw:recordPacking>
    <srw:recordSchema>schema</srw:recordSchema>
</srw:echoedSearchRetrieveRequest>""", result)

    def testEchoedSearchRetrieveRequestWithExtraXParameters(self):
        arguments = {'version':'1.1', 'operation':'searchRetrieve', 'query':'query >= 3', 'recordSchema':'schema', 'recordPacking':'string', 'x_link_filter': 'True'}
        component = SruHandler(extraXParameters=['x-link-filter'])

        result = "".join(list(component._writeEchoedSearchRetrieveRequest(**arguments)))
        self.assertEqualsWS("""<srw:echoedSearchRetrieveRequest>
    <srw:version>1.1</srw:version>
    <srw:query>query &gt;= 3</srw:query>
    <srw:recordPacking>string</srw:recordPacking>
    <srw:recordSchema>schema</srw:recordSchema>
    <srw:x-link-filter>True</srw:x-link-filter>
</srw:echoedSearchRetrieveRequest>""", result)

    def testEchoedSearchRetrieveRequestWithExtraRequestData(self):
        arguments = {'version':'1.1', 'operation':'searchRetrieve', 'query':'query >= 3', 'recordSchema':'schema', 'recordPacking':'string', 'x_term_drilldown':['field0,field1']}
        observer = CallTrace('ExtraRequestData')
        observer.methods['echoedExtraRequestData'] = lambda *a, **kw: (x for x in '<some>extra request data</some>')
        component = SruHandler()
        component.addObserver(SRUTermDrilldown())
        component.addObserver(observer)

        result = "".join(list(component._writeEchoedSearchRetrieveRequest(**arguments)))
        
        drilldownRequestData = DRILLDOWN_HEADER \
        + """<dd:term-drilldown>field0,field1</dd:term-drilldown>"""\
        + DRILLDOWN_FOOTER
        self.assertEqualsWS("""<srw:echoedSearchRetrieveRequest>
    <srw:version>1.1</srw:version>
    <srw:query>query &gt;= 3</srw:query>
    <srw:recordPacking>string</srw:recordPacking>
    <srw:recordSchema>schema</srw:recordSchema>
    <srw:extraRequestData>%s<some>extra request data</some></srw:extraRequestData>
</srw:echoedSearchRetrieveRequest>""" % drilldownRequestData, result)

    def testExtraResponseDataHandlerNoHandler(self):
        component = SruHandler()
        result = "".join(list(component._writeExtraResponseData(cqlAbstractSyntaxTree=None)))
        self.assertEquals('' , result)

    def testExtraResponseDataHandlerNoData(self):
        class TestHandler:
            def extraResponseData(self, *args, **kwargs):
                return (f for f in [])

        component = SruHandler()
        component.addObserver(TestHandler())
        result = "".join(list(component._writeExtraResponseData(cqlAbstractSyntaxTree=None)))
        self.assertEquals('' , result)

    def testExtraResponseDataHandlerWithData(self):
        argsUsed = []
        kwargsUsed = {}
        class TestHandler:
            def extraResponseData(self, *args, **kwargs):
                argsUsed.append(args)
                kwargsUsed.update(kwargs)
                return (f for f in ["<someD", "ata/>"])

        component = SruHandler()
        component.addObserver(TestHandler())
        result = "".join(list(component._writeExtraResponseData(cqlAbstractSyntaxTree=None)))
        self.assertEquals('<srw:extraResponseData><someData/></srw:extraResponseData>' , result)
        self.assertEquals([()], argsUsed)
        self.assertEquals(None, kwargsUsed['cqlAbstractSyntaxTree'])
        self.assertEquals(None, kwargsUsed['queryTime'])
        self.assertEquals(None, kwargsUsed['response'])

    def testExtraResponseDataWithTermDrilldown(self):
        arguments = {'version':'1.1', 'operation':'searchRetrieve', 'query':'query >= 3', 'recordSchema':'schema', 'recordPacking':'string', 'x_term_drilldown':['field0,field1']}

        sruHandler = SruHandler()
        sruTermDrilldown = SRUTermDrilldown()
        drilldownData = iter([
                ('field0', iter([('value0_0', 14)])),
                ('field1', iter([('value1_0', 13), ('value1_1', 11)])),
                ('field2', iter([('value2_0', 3), ('value2_1', 2), ('value2_2', 1)]))
            ])
        sruHandler.addObserver(sruTermDrilldown)
        result = "".join(sruHandler._writeExtraResponseData(drilldownData=drilldownData, **arguments))
        self.assertEqualsWS("""<srw:extraResponseData><dd:drilldown\n    xmlns:dd="http://meresco.org/namespace/drilldown"\n    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n    xsi:schemaLocation="http://meresco.org/namespace/drilldown http://meresco.org/files/xsd/drilldown-20070730.xsd"><dd:term-drilldown><dd:navigator name="field0"><dd:item count="14">value0_0</dd:item></dd:navigator><dd:navigator name="field1"><dd:item count="13">value1_0</dd:item><dd:item count="11">value1_1</dd:item></dd:navigator><dd:navigator name="field2"><dd:item count="3">value2_0</dd:item><dd:item count="2">value2_1</dd:item><dd:item count="1">value2_2</dd:item></dd:navigator></dd:term-drilldown></dd:drilldown></srw:extraResponseData>""" , result)

    def testDrilldownResultInExecuteQuery(self):
        observer = CallTrace()
        response = Response(total=100, hits=hitsRange(11, 26))
        drilldownData = iter([
            ('field0', iter([('value0_0', 14)])),
            ('field1', iter([('value1_0', 13), ('value1_1', 11)])),
            ('field2', iter([('value2_0', 3), ('value2_1', 2), ('value2_2', 1)]))]) 
        response.drilldownData = drilldownData
        def executeQuery(**kwargs):
            raise StopIteration(response)
            yield
        observer.methods['executeQuery'] = executeQuery
        observer.methods['yieldRecord'] = lambda *a, **kw: (x for x in 'record')
        observer.methods['extraResponseData'] = lambda *a, **kw: (x for x in 'extraResponseData')
        observer.methods['echoedExtraRequestData'] = lambda *a, **kw: (x for x in 'echoedExtraRequestData')

        component = SruHandler()
        component.addObserver(observer)

        result = "".join(compose(component.searchRetrieve(startRecord=11, maximumRecords=15, query='query', recordPacking='string', recordSchema='schema', x_term_drilldown=["field0:1,fie:ld1:2,field2,fie:ld3"])))
        self.assertEquals(['executeQuery'] + ['yieldRecord'] * 15 + ['echoedExtraRequestData', 'extraResponseData'], [m.name for m in observer.calledMethods])
        self.assertEquals([('field0', 1, False), ('fie:ld1', 2, False), ('field2', DEFAULT_MAXIMUM_TERMS, False), ('fie:ld3', DEFAULT_MAXIMUM_TERMS, False)], list(observer.calledMethods[0].kwargs['fieldnamesAndMaximums']))
        extraResponseDataMethod = observer.calledMethods[-1]
        self.assertEquals(response, extraResponseDataMethod.kwargs['response'])

    def testNextRecordPosition(self):
        observer = CallTrace()
        response = Response(total=100, hits=hitsRange(11, 26))
        def executeQuery(**kwargs):
            raise StopIteration(response)
            yield
        observer.methods['executeQuery'] = executeQuery
        observer.returnValues['yieldRecord'] = lambda *a, **kw: (x for x in "record")
        observer.methods['extraResponseData'] = lambda *a, **kw: (x for x in 'extraResponseData')
        observer.methods['echoedExtraRequestData'] = lambda *a, **kw: (x for x in 'echoedExtraRequestData')

        component = SruHandler()
        component.addObserver(observer)

        result = "".join(compose(component.searchRetrieve(startRecord=11, maximumRecords=15, query='query', recordPacking='string', recordSchema='schema')))
        self.assertTrue("<srw:nextRecordPosition>26</srw:nextRecordPosition>" in result, result)

        executeCqlCallKwargs = observer.calledMethods[0].kwargs
        self.assertEquals(10, executeCqlCallKwargs['start']) # SRU is 1 based
        self.assertEquals(25, executeCqlCallKwargs['stop'])
    
    def testSearchRetrieveVersion11(self):
        arguments = {'version':'1.1', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2, 'x_recordSchema':['extra', 'evenmore']}

        observer = CallTrace()
        response = Response(total=100, hits=hitsRange(11, 13))
        def executeQuery(**kwargs):
            raise StopIteration(response)
            yield
        observer.methods['executeQuery'] = executeQuery

        yieldRecordCalls = []
        def yieldRecord(identifier, partname):
            yieldRecordCalls.append(1)
            yield "<MOCKED_WRITTEN_DATA>%s-%s</MOCKED_WRITTEN_DATA>" % (xmlEscape(identifier), partname)
        observer.yieldRecord = yieldRecord

        observer.methods['extraResponseData'] = lambda *a, **kw: (x for x in 'extraResponseData')
        observer.methods['echoedExtraRequestData'] = lambda *a, **kw: (x for x in 'echoedExtraRequestData')

        component = SruHandler()
        component.addObserver(observer)

        result = "".join(compose(component.searchRetrieve(**arguments)))

        self.assertEqualsWS("""
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <srw:version>1.1</srw:version>
    <srw:numberOfRecords>100</srw:numberOfRecords>
    <srw:records>
        <srw:record>
            <srw:recordSchema>schema</srw:recordSchema>
            <srw:recordPacking>xml</srw:recordPacking>
            <srw:recordData>
                <MOCKED_WRITTEN_DATA>11-schema</MOCKED_WRITTEN_DATA>
            </srw:recordData>
            <srw:extraRecordData>
                <srw:record>
                    <srw:recordSchema>extra</srw:recordSchema>
                    <srw:recordPacking>xml</srw:recordPacking>
                    <srw:recordData>
                    <MOCKED_WRITTEN_DATA>11-extra</MOCKED_WRITTEN_DATA>
                    </srw:recordData>
                </srw:record>
                <srw:record>
                    <srw:recordSchema>evenmore</srw:recordSchema>
                    <srw:recordPacking>xml</srw:recordPacking>
                    <srw:recordData>
                    <MOCKED_WRITTEN_DATA>11-evenmore</MOCKED_WRITTEN_DATA>
                    </srw:recordData>
                </srw:record>
            </srw:extraRecordData>
        </srw:record>
        <srw:record>
            <srw:recordSchema>schema</srw:recordSchema>
            <srw:recordPacking>xml</srw:recordPacking>
            <srw:recordData>
                <MOCKED_WRITTEN_DATA>12-schema</MOCKED_WRITTEN_DATA>
            </srw:recordData>
            <srw:extraRecordData>
                <srw:record>
                    <srw:recordSchema>extra</srw:recordSchema>
                    <srw:recordPacking>xml</srw:recordPacking>
                    <srw:recordData>
                    <MOCKED_WRITTEN_DATA>12-extra</MOCKED_WRITTEN_DATA>
                    </srw:recordData>
                </srw:record>
                <srw:record>
                    <srw:recordSchema>evenmore</srw:recordSchema>
                    <srw:recordPacking>xml</srw:recordPacking>
                    <srw:recordData>
                    <MOCKED_WRITTEN_DATA>12-evenmore</MOCKED_WRITTEN_DATA>
                    </srw:recordData>
                </srw:record>
            </srw:extraRecordData>
        </srw:record>
    </srw:records>
    <srw:nextRecordPosition>3</srw:nextRecordPosition>
    <srw:echoedSearchRetrieveRequest>
        <srw:version>1.1</srw:version>
        <srw:query>field=value</srw:query>
        <srw:startRecord>1</srw:startRecord>
        <srw:maximumRecords>2</srw:maximumRecords>
        <srw:recordPacking>xml</srw:recordPacking>
        <srw:recordSchema>schema</srw:recordSchema>
        <srw:x-recordSchema>extra</srw:x-recordSchema>
        <srw:x-recordSchema>evenmore</srw:x-recordSchema>
        <srw:extraRequestData>echoedExtraRequestData</srw:extraRequestData>
    </srw:echoedSearchRetrieveRequest>
    <srw:extraResponseData>extraResponseData</srw:extraResponseData>
</srw:searchRetrieveResponse>
""", result)

    def testSearchRetrieveVersion12(self):
        arguments = {'version':'1.2', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2, 'x_recordSchema':['extra', 'evenmore'], 'x_extra_key': 'extraValue'}

        observer = CallTrace()
        response = Response(total=100, hits=['<aap&noot>', 'vuur'])
        def executeQuery(**kwargs):
            raise StopIteration(response)
            yield
        observer.methods['executeQuery'] = executeQuery

        yieldRecordCalls = []
        def yieldRecord(identifier, partname):
            yieldRecordCalls.append(1)
            yield "<MOCKED_WRITTEN_DATA>%s-%s</MOCKED_WRITTEN_DATA>" % (xmlEscape(identifier), partname)
        observer.yieldRecord = yieldRecord

        observer.methods['extraResponseData'] = lambda *a, **kw: (x for x in 'extraResponseData')
        observer.methods['echoedExtraRequestData'] = lambda *a, **kw: (x for x in 'echoedExtraRequestData')

        component = SruHandler()
        component.addObserver(observer)

        result = "".join(compose(component.searchRetrieve(**arguments)))
        self.assertEquals(['executeQuery', 'echoedExtraRequestData', 'extraResponseData'], [m.name for m in observer.calledMethods])
        executeQueryMethod, echoedExtraRequestDataMethod, extraResponseDataMethod = observer.calledMethods
        self.assertEquals('executeQuery', executeQueryMethod.name)
        methodKwargs = executeQueryMethod.kwargs
        self.assertEquals(parseString('field=value'), methodKwargs['cqlAbstractSyntaxTree'])
        self.assertEquals(0, methodKwargs['start'])
        self.assertEquals(2, methodKwargs['stop'])
        self.assertEquals('extraValue', methodKwargs['x_extra_key'])
        self.assertEquals(0, methodKwargs['suggestionsCount'])

        self.assertEquals(6, sum(yieldRecordCalls))

        resultXml = parse(StringIO(result))
        ids = resultXml.xpath('//srw:recordIdentifier/text()', namespaces={'srw':"http://www.loc.gov/zing/srw/"})
        self.assertEquals(['<aap&noot>', 'vuur'], ids)

        self.assertEqualsWS("""
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <srw:version>1.2</srw:version>
    <srw:numberOfRecords>100</srw:numberOfRecords>
    <srw:records>
        <srw:record>
            <srw:recordSchema>schema</srw:recordSchema>
            <srw:recordPacking>xml</srw:recordPacking>
            <srw:recordIdentifier>&lt;aap&amp;noot&gt;</srw:recordIdentifier>
            <srw:recordData>
                <MOCKED_WRITTEN_DATA>&lt;aap&amp;noot&gt;-schema</MOCKED_WRITTEN_DATA>
            </srw:recordData>
            <srw:extraRecordData>
                <srw:record>
                    <srw:recordSchema>extra</srw:recordSchema>
                    <srw:recordPacking>xml</srw:recordPacking>
                    <srw:recordData>
                    <MOCKED_WRITTEN_DATA>&lt;aap&amp;noot&gt;-extra</MOCKED_WRITTEN_DATA>
                    </srw:recordData>
                </srw:record>
                <srw:record>
                    <srw:recordSchema>evenmore</srw:recordSchema>
                    <srw:recordPacking>xml</srw:recordPacking>
                    <srw:recordData>
                    <MOCKED_WRITTEN_DATA>&lt;aap&amp;noot&gt;-evenmore</MOCKED_WRITTEN_DATA>
                    </srw:recordData>
                </srw:record>
            </srw:extraRecordData>
        </srw:record>
        <srw:record>
            <srw:recordSchema>schema</srw:recordSchema>
            <srw:recordPacking>xml</srw:recordPacking>
            <srw:recordIdentifier>vuur</srw:recordIdentifier>
            <srw:recordData>
                <MOCKED_WRITTEN_DATA>vuur-schema</MOCKED_WRITTEN_DATA>
            </srw:recordData>
            <srw:extraRecordData>
                <srw:record>
                    <srw:recordSchema>extra</srw:recordSchema>
                    <srw:recordPacking>xml</srw:recordPacking>
                    <srw:recordData>
                    <MOCKED_WRITTEN_DATA>vuur-extra</MOCKED_WRITTEN_DATA>
                    </srw:recordData>
                </srw:record>
                <srw:record>
                    <srw:recordSchema>evenmore</srw:recordSchema>
                    <srw:recordPacking>xml</srw:recordPacking>
                    <srw:recordData>
                    <MOCKED_WRITTEN_DATA>vuur-evenmore</MOCKED_WRITTEN_DATA>
                    </srw:recordData>
                </srw:record>
            </srw:extraRecordData>
        </srw:record>
    </srw:records>
    <srw:nextRecordPosition>3</srw:nextRecordPosition>
    <srw:echoedSearchRetrieveRequest>
        <srw:version>1.2</srw:version>
        <srw:query>field=value</srw:query>
        <srw:startRecord>1</srw:startRecord>
        <srw:maximumRecords>2</srw:maximumRecords>
        <srw:recordPacking>xml</srw:recordPacking>
        <srw:recordSchema>schema</srw:recordSchema>
        <srw:x-recordSchema>extra</srw:x-recordSchema>
        <srw:x-recordSchema>evenmore</srw:x-recordSchema>
        <srw:extraRequestData>echoedExtraRequestData</srw:extraRequestData>
    </srw:echoedSearchRetrieveRequest>
    <srw:extraResponseData>extraResponseData</srw:extraResponseData>
</srw:searchRetrieveResponse>
""", result)
        
        self.assertEquals((), echoedExtraRequestDataMethod.args)
        self.assertEquals(set(['version', 'x_term_drilldown', 'recordSchema', 'x_recordSchema', 'sortDescending', 'sortBy', 'maximumRecords', 'startRecord', 'query', 'operation', 'recordPacking', 'x_extra_key']), set(echoedExtraRequestDataMethod.kwargs.keys()))
        self.assertEquals((), extraResponseDataMethod.args)
        self.assertEquals(set(['version', 'recordSchema', 'x_recordSchema', 'sortDescending', 'sortBy', 'maximumRecords', 'startRecord', 'query', 'operation', 'recordPacking', 'cqlAbstractSyntaxTree', 'response', 'drilldownData', 'x_extra_key', 'queryTime']), set(extraResponseDataMethod.kwargs.keys()))
 
    def testExtraRecordDataOldStyle(self):
        arguments = {'version':'1.2', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2, 'x_recordSchema':['extra', 'evenmore']}

        observer = CallTrace()
        response = Response(total=100, hits=['11'])
        def executeQuery(**kwargs):
            raise StopIteration(response)
            yield
        observer.methods['executeQuery'] = executeQuery

        yieldRecordCalls = []
        def yieldRecord(identifier, partname):
            yieldRecordCalls.append(1)
            yield "<MOCKED_WRITTEN_DATA>%s-%s</MOCKED_WRITTEN_DATA>" % (identifier, partname)
        observer.yieldRecord = yieldRecord

        observer.methods['extraResponseData'] = lambda *a, **kw: (x for x in 'extraResponseData')
        observer.methods['echoedExtraRequestData'] = lambda *a, **kw: (x for x in 'echoedExtraRequestData')
        component = SruHandler(extraRecordDataNewStyle=False)
        component.addObserver(observer)

        result = "".join(compose(component.searchRetrieve(**arguments)))

        strippedResult = result[result.index('<srw:record>'):result.index('</srw:records>')]
        self.assertEqualsWS("""<srw:record>
            <srw:recordSchema>schema</srw:recordSchema>
            <srw:recordPacking>xml</srw:recordPacking>
            <srw:recordIdentifier>11</srw:recordIdentifier>
            <srw:recordData>
                <MOCKED_WRITTEN_DATA>11-schema</MOCKED_WRITTEN_DATA>
            </srw:recordData>
            <srw:extraRecordData>
                <recordData recordSchema="extra">
                    <MOCKED_WRITTEN_DATA>11-extra</MOCKED_WRITTEN_DATA>
                </recordData>
                <recordData recordSchema="evenmore">
                    <MOCKED_WRITTEN_DATA>11-evenmore</MOCKED_WRITTEN_DATA>
                </recordData>
            </srw:extraRecordData>
        </srw:record>""", strippedResult)

    def testRecordPackingXmlAndSuspendObjects(self):
        def Suspend():
            pass
        def yieldRecord(**kwargs):
            yield '<tag>'
            yield Suspend
            yield '</tag>'
        observer = CallTrace('observer')
        observer.methods['yieldRecord'] = yieldRecord
        component = SruHandler()
        component.addObserver(observer)

        result = list(compose(component._writeRecordData(recordSchema='schema', recordPacking='string', recordId='identifier')))
        self.assertEquals(['<srw:recordData>',
            '&lt;tag&gt;',
            Suspend,
            '&lt;/tag&gt;',
            '</srw:recordData>'], result)

    def testIOErrorInWriteRecordData(self):
        observer = CallTrace()
        observer.exceptions["yieldRecord"] = IOError()
        component = SruHandler()
        component.addObserver(observer)
        result = "".join(list(compose(component._writeRecordData(recordPacking="string", recordSchema="schema", recordId="ID"))))
        self.assertTrue("diagnostic" in result, result)
        self.assertTrue("recordSchema 'schema' for identifier 'ID' does not exist" in result, result)

    def testExceptionInWriteRecordData(self):
        observer = CallTrace()
        observer.exceptions["yieldRecord"] = Exception("Test Exception")
        component = SruHandler()
        component.addObserver(observer)
        result = "".join(list(compose(component._writeRecordData(recordPacking="string", recordSchema="schema", recordId="ID"))))
        self.assertTrue("diagnostic" in result, result)
        self.assertTrue("Test Exception" in result, result)

    def testExceptionInWriteExtraRecordData(self):
        class RaisesException(object):
            def extraResponseData(self, *args, **kwargs):
                raise Exception("Test Exception")
        component = SruHandler()
        component.addObserver(RaisesException())
        result = "".join(compose(component._writeExtraResponseData(cqlAbstractSyntaxTree=None)))
        self.assertTrue("diagnostic" in result)

    def testDiagnosticOnExecuteCql(self):
        sys.stderr = StringIO()
        try:
            class RaisesException(object):
                def executeQuery(self, *args, **kwargs):
                    raise Exception("Test Exception")
            component = SruHandler()
            component.addObserver(RaisesException())
            result = "".join(compose(component.searchRetrieve(startRecord=11, maximumRecords=15, query='query', recordPacking='string', recordSchema='schema')))
            self.assertTrue("diagnostic" in result)
        finally:
            sys.stderr = sys.__stderr__
    
    def testValidXml(self):
        component = SruParser()
        sruHandler = SruHandler()
        component.addObserver(sruHandler)
        observer = CallTrace('observer')
        sruHandler.addObserver(observer)
        response = Response(total=2, hits=['id0', 'id1'])
        def executeQuery(**kwargs):
            raise StopIteration(response)
            yield
        observer.methods['executeQuery'] = executeQuery
        observer.returnValues['echoedExtraRequestData'] = (f for f in [])
        observer.returnValues['extraResponseData'] = (f for f in [])
        observer.methods['yieldRecord'] = lambda *args, **kwargs: (x for x in '<bike/>')

        result = ''.join(compose(component.handleRequest(arguments={'version':['1.1'], 'query': ['aQuery'], 'operation':['searchRetrieve']})))
        header, body = result.split('\r\n'*2)
        assertValid(body, join(schemasPath, 'srw-types1.2.xsd'))
        self.assertTrue('<bike/>' in body, body)
        
        result = ''.join(compose(component.handleRequest(arguments={'version':['1.1'], 'operation':['searchRetrieve']})))
        header, body = result.split('\r\n'*2)
        assertValid(body, join(schemasPath, 'srw-types1.2.xsd'))
        self.assertTrue('diagnostic' in body, body)


    def testQueryTimeInExtraResponse(self):
        handler = SruHandler(includeQueryTimes=True)
        observer = CallTrace('observer', emptyGeneratorMethods=['echoedExtraRequestData', 'extraResponseData'])

        times = [1, 2.5]
        def timeNow():
            return times.pop(0)
        handler._timeNow = timeNow

        def executeQuery(**kwargs):
            response = Response(total=0, hits=[])
            response.queryTime=5
            raise StopIteration(response)
            yield
        observer.methods['executeQuery'] = executeQuery
        handler.addObserver(observer)
        result = "".join(compose(handler.searchRetrieve(startRecord=11, maximumRecords=15, query='query', recordPacking='string', recordSchema='schema')))
        sruResponse = parse(StringIO(result))
        extraResponseData = sruResponse.xpath('/srw:searchRetrieveResponse/srw:extraResponseData', namespaces={'srw':"http://www.loc.gov/zing/srw/"})[0]
        self.assertEqualsWS("""<srw:extraResponseData xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/">
        <querytimes xmlns="http://meresco.org/namespace/timing">        
            <sru>PT1.500S</sru>        
            <index>PT0.005S</index>    
        </querytimes>
</srw:extraResponseData>""", tostring(extraResponseData))
        queryTimes = tostring(extraResponseData.xpath('//ti:querytimes', namespaces={'ti':"http://meresco.org/namespace/timing"})[0])
        assertValid(queryTimes, join(schemasPath, 'timing-20120827.xsd'))

    def testTestXSDequalsPublishedXSD(self):
        xsd = urlopen("http://meresco.org/files/xsd/timing-20120827.xsd").read()
        localxsd = open(join(schemasPath, 'timing-20120827.xsd')).read()
        self.assertEqualsWS(xsd, localxsd)

    def testSearchRetrieveWithSuggestions(self):
        arguments = {'version':'1.2', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2, 'x_recordSchema':['extra', 'evenmore'], 'x_extra_key': 'extraValue'}

        observer = CallTrace(emptyGeneratorMethods=['extraResponseData', 'echoedExtraRequestData'])
        response = Response(total=0, hits=[])
        def executeQuery(**kwargs):
            raise StopIteration(response)
            yield
        observer.methods['executeQuery'] = executeQuery

        handler = SruHandler(querySuggestionsCount=5)
        handler.addObserver(observer)

        result = "".join(compose(handler.searchRetrieve(**arguments)))
        self.assertEquals(['executeQuery', 'echoedExtraRequestData', 'extraResponseData'], [m.name for m in observer.calledMethods])
        executeQueryMethod, echoedExtraRequestDataMethod, extraResponseDataMethod = observer.calledMethods
        self.assertEquals('executeQuery', executeQueryMethod.name)
        methodKwargs = executeQueryMethod.kwargs
        self.assertEquals(5, methodKwargs['suggestionsCount'])

def hitsRange(*args):
    return ['%s' % i for i in range(*args)]
