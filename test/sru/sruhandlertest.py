# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#    Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from meresco.components.sru.sruparser import MANDATORY_PARAMETER_NOT_SUPPLIED, UNSUPPORTED_PARAMETER, UNSUPPORTED_VERSION, UNSUPPORTED_OPERATION, UNSUPPORTED_PARAMETER_VALUE, QUERY_FEATURE_UNSUPPORTED, SruException

from meresco.components.sru import SruHandler, SruParser
from meresco.components.drilldown import SRUTermDrilldown, DRILLDOWN_HEADER, DRILLDOWN_FOOTER
from meresco.components.xml_generic.validate import assertValid
from meresco.components.xml_generic import schemasPath

from os.path import join


from StringIO import StringIO
from cq2utils import CQ2TestCase, CallTrace
from cqlparser import parseString
import traceback

from weightless.core import compose

SUCCESS = "SUCCESS"

class SruHandlerTest(CQ2TestCase):

    def testEchoedSearchRetrieveRequest(self):
        arguments = {'version':'1.1', 'operation':'searchRetrieve', 'query':'query >= 3', 'recordSchema':'schema', 'recordPacking':'string'}
        component = SruHandler(extraRecordDataNewStyle=True)

        result = "".join(list(component._writeEchoedSearchRetrieveRequest(**arguments)))
        self.assertEqualsWS("""<srw:echoedSearchRetrieveRequest>
    <srw:version>1.1</srw:version>
    <srw:query>query &gt;= 3</srw:query>
    <srw:recordPacking>string</srw:recordPacking>
    <srw:recordSchema>schema</srw:recordSchema>
</srw:echoedSearchRetrieveRequest>""", result)

    def testEchoedSearchRetrieveRequestWithExtraRequestData(self):
        arguments = {'version':'1.1', 'operation':'searchRetrieve', 'query':'query >= 3', 'recordSchema':'schema', 'recordPacking':'string', 'x_term_drilldown':['field0,field1']}
        observer = CallTrace('ExtraRequestData', returnValues={'echoedExtraRequestData': '<some>extra request data</some>'})
        component = SruHandler(extraRecordDataNewStyle=True)
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
        component = SruHandler(extraRecordDataNewStyle=True)
        result = "".join(list(component._writeExtraResponseData(cqlAbstractSyntaxTree=None)))
        self.assertEquals('' , result)

    def testExtraResponseDataHandlerNoData(self):
        class TestHandler:
            def extraResponseData(self, *args, **kwargs):
                return (f for f in [])

        component = SruHandler(extraRecordDataNewStyle=True)
        component.addObserver(TestHandler())
        result = "".join(list(component._writeExtraResponseData(cqlAbstractSyntaxTree=None)))
        self.assertEquals('' , result)

    def testExtraResponseDataHandlerWithData(self):
        argsUsed = []
        kwargsUsed = []
        class TestHandler:
            def extraResponseData(self, *args, **kwargs):
                argsUsed.append(args)
                kwargsUsed.append(kwargs)
                return (f for f in ["<someD", "ata/>"])

        component = SruHandler(extraRecordDataNewStyle=True)
        component.addObserver(TestHandler())
        result = "".join(list(component._writeExtraResponseData(cqlAbstractSyntaxTree=None)))
        self.assertEquals('<srw:extraResponseData><someData/></srw:extraResponseData>' , result)
        self.assertEquals([()], argsUsed)
        self.assertEquals([{'cqlAbstractSyntaxTree': None}], kwargsUsed)

    def testExtraResponseDataWithTermDrilldown(self):
        arguments = {'version':'1.1', 'operation':'searchRetrieve', 'query':'query >= 3', 'recordSchema':'schema', 'recordPacking':'string', 'x_term_drilldown':['field0,field1']}

        sruHandler = SruHandler()
        sruTermDrilldown = SRUTermDrilldown()
        observer = CallTrace("Drilldown")
        observer.returnValues['drilldown'] = iter([
                ('field0', iter([('value0_0', 14)])),
                ('field1', iter([('value1_0', 13), ('value1_1', 11)])),
                ('field2', iter([('value2_0', 3), ('value2_1', 2), ('value2_2', 1)]))
            ])
        sruTermDrilldown.addObserver(observer)
        sruHandler.addObserver(sruTermDrilldown)
        result = "".join(list(sruHandler._writeExtraResponseData(docset='docset', **arguments)))
        self.assertEqualsWS("""<srw:extraResponseData><dd:drilldown\n    xmlns:dd="http://meresco.org/namespace/drilldown"\n    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n    xsi:schemaLocation="http://meresco.org/namespace/drilldown http://meresco.org/files/xsd/drilldown-20070730.xsd"><dd:term-drilldown><dd:navigator name="field0"><dd:item count="14">value0_0</dd:item></dd:navigator><dd:navigator name="field1"><dd:item count="13">value1_0</dd:item><dd:item count="11">value1_1</dd:item></dd:navigator><dd:navigator name="field2"><dd:item count="3">value2_0</dd:item><dd:item count="2">value2_1</dd:item><dd:item count="1">value2_2</dd:item></dd:navigator></dd:term-drilldown></dd:drilldown></srw:extraResponseData>""" , result)

    def testNextRecordPosition(self):
        observer = CallTrace()
        observer.exceptions['executeCQL'] = StopIteration([100, range(11, 26)])
        observer.returnValues['yieldRecord'] = "record"
        observer.returnValues['extraResponseData'] = 'extraResponseData'
        observer.returnValues['echoedExtraRequestData'] = 'echoedExtraRequestData'

        component = SruHandler(extraRecordDataNewStyle=True)
        component.addObserver(observer)

        result = "".join(compose(component.searchRetrieve(startRecord=11, maximumRecords=15, query='query', recordPacking='string', recordSchema='schema')))
        self.assertTrue("<srw:nextRecordPosition>26</srw:nextRecordPosition>" in result, result)

        executeCqlCallKwargs = observer.calledMethods[0].kwargs
        self.assertEquals(10, executeCqlCallKwargs['start']) # SRU is 1 based
        self.assertEquals(25, executeCqlCallKwargs['stop'])
    
    def testSearchRetrieveVersion11(self):
        arguments = {'version':'1.1', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2, 'x_recordSchema':['extra', 'evenmore']}

        observer = CallTrace()
        observer.exceptions['executeCQL'] = StopIteration([100, range(11, 13)])

        yieldRecordCalls = []
        def yieldRecord(recordId, recordSchema):
            yieldRecordCalls.append(1)
            yield "<MOCKED_WRITTEN_DATA>%s-%s</MOCKED_WRITTEN_DATA>" % (recordId, recordSchema)
        observer.yieldRecord = yieldRecord

        observer.returnValues['extraResponseData'] = 'extraResponseData'
        observer.returnValues['echoedExtraRequestData'] = 'echoedExtraRequestData'

        component = SruHandler(extraRecordDataNewStyle=True)
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
        arguments = {'version':'1.2', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2, 'x_recordSchema':['extra', 'evenmore']}

        observer = CallTrace()
        observer.exceptions['executeCQL'] = StopIteration([100, range(11, 13)])

        yieldRecordCalls = []
        def yieldRecord(recordId, recordSchema):
            yieldRecordCalls.append(1)
            yield "<MOCKED_WRITTEN_DATA>%s-%s</MOCKED_WRITTEN_DATA>" % (recordId, recordSchema)
        observer.yieldRecord = yieldRecord

        observer.returnValues['extraResponseData'] = 'extraResponseData'
        observer.returnValues['echoedExtraRequestData'] = 'echoedExtraRequestData'

        component = SruHandler(extraRecordDataNewStyle=True)
        component.addObserver(observer)

        result = "".join(compose(component.searchRetrieve(**arguments)))
        self.assertEquals(['executeCQL', 'docsetFromQuery', 'echoedExtraRequestData', 'extraResponseData'], [m.name for m in observer.calledMethods])
        executeCQLMethod, docsetFromQueryMethod, echoedExtraRequestDataMethod, extraResponseDataMethod = observer.calledMethods
        self.assertEquals('executeCQL', executeCQLMethod.name)
        methodKwargs = executeCQLMethod.kwargs
        self.assertEquals(parseString('field=value'), methodKwargs['cqlAbstractSyntaxTree'])
        self.assertEquals(0, methodKwargs['start'])
        self.assertEquals(2, methodKwargs['stop'])

        self.assertEquals(6, sum(yieldRecordCalls))

        self.assertEqualsWS("""
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <srw:version>1.2</srw:version>
    <srw:numberOfRecords>100</srw:numberOfRecords>
    <srw:records>
        <srw:record>
            <srw:recordSchema>schema</srw:recordSchema>
            <srw:recordPacking>xml</srw:recordPacking>
            <srw:recordIdentifier>11</srw:recordIdentifier>
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
            <srw:recordIdentifier>12</srw:recordIdentifier>
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
        self.assertEquals(['version', 'recordSchema', 'x_recordSchema', 'sortDescending', 'sortBy', 'maximumRecords', 'startRecord', 'query', 'operation', 'recordPacking'], echoedExtraRequestDataMethod.kwargs.keys())
        self.assertEquals((), extraResponseDataMethod.args)
        self.assertEquals(set(['version', 'recordSchema', 'x_recordSchema', 'sortDescending', 'sortBy', 'maximumRecords', 'startRecord', 'query', 'operation', 'recordPacking', 'cqlAbstractSyntaxTree', 'docset']), set(extraResponseDataMethod.kwargs.keys()))

    def testExtraRecordDataOldStyle(self):
        arguments = {'version':'1.2', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2, 'x_recordSchema':['extra', 'evenmore']}

        observer = CallTrace()
        observer.exceptions['executeCQL'] = StopIteration([100, [11]])

        yieldRecordCalls = []
        def yieldRecord(recordId, recordSchema):
            yieldRecordCalls.append(1)
            yield "<MOCKED_WRITTEN_DATA>%s-%s</MOCKED_WRITTEN_DATA>" % (recordId, recordSchema)
        observer.yieldRecord = yieldRecord

        observer.returnValues['extraResponseData'] = 'extraResponseData'
        observer.returnValues['echoedExtraRequestData'] = 'echoedExtraRequestData'
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

    def testIOErrorInWriteRecordData(self):
        observer = CallTrace()
        observer.exceptions["yieldRecord"] = IOError()
        component = SruHandler(extraRecordDataNewStyle=True)
        component.addObserver(observer)
        result = "".join(list(compose(component._writeRecordData(recordPacking="string", recordSchema="schema", recordId="ID"))))
        self.assertTrue("diagnostic" in result, result)
        self.assertTrue("recordSchema 'schema' for identifier 'ID' does not exist" in result, result)

    def testExceptionInWriteRecordData(self):
        observer = CallTrace()
        observer.exceptions["yieldRecord"] = Exception("Test Exception")
        component = SruHandler(extraRecordDataNewStyle=True)
        component.addObserver(observer)
        result = "".join(list(compose(component._writeRecordData(recordPacking="string", recordSchema="schema", recordId="ID"))))
        self.assertTrue("diagnostic" in result, result)
        self.assertTrue("Test Exception" in result, result)

    def testExceptionInWriteExtraRecordData(self):
        class RaisesException(object):
            def extraResponseData(self, *args, **kwargs):
                raise Exception("Test Exception")
        component = SruHandler(extraRecordDataNewStyle=True)
        component.addObserver(RaisesException())
        result = "".join(compose(component._writeExtraResponseData(cqlAbstractSyntaxTree=None)))
        self.assertTrue("diagnostic" in result)

    def testDiagnosticOnExecuteCql(self):
        class RaisesException(object):
            def executeCQL(self, *args, **kwargs):
                raise Exception("Test Exception")
        component = SruHandler(extraRecordDataNewStyle=True)
        component.addObserver(RaisesException())
        result = "".join(compose(component.searchRetrieve(startRecord=11, maximumRecords=15, query='query', recordPacking='string', recordSchema='schema')))
        self.assertTrue("diagnostic" in result)

    
    def testValidXml(self):
        component = SruParser()
        sruHandler = SruHandler()
        component.addObserver(sruHandler)
        observer = CallTrace('observer')
        sruHandler.addObserver(observer)
        observer.exceptions['executeCQL'] = StopIteration([2, ['id0', 'id1']])
        observer.returnValues['echoedExtraRequestData'] = (f for f in [])
        observer.returnValues['extraResponseData'] = (f for f in [])
        observer.methods['yieldRecord'] = lambda *args, **kwargs: '<bike/>'

        result = ''.join(compose(component.handleRequest(arguments={'version':['1.1'], 'query': ['aQuery'], 'operation':['searchRetrieve']})))
        header, body = result.split('\r\n'*2)
        assertValid(body, join(schemasPath, 'srw-types1.2.xsd'))
        self.assertTrue('<bike/>' in body)
        
        result = ''.join(compose(component.handleRequest(arguments={'version':['1.1'], 'operation':['searchRetrieve']})))
        header, body = result.split('\r\n'*2)
        assertValid(body, join(schemasPath, 'srw-types1.2.xsd'))
        self.assertTrue('diagnostic' in body)

