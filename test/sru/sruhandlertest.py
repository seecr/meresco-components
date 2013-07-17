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
# Copyright (C) 2011-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011-2013 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2012-2013 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
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

from lxml.etree import parse
from meresco.components import lxmltostring
from xml.sax.saxutils import escape as xmlEscape

from weightless.core import compose, be

from cqlparser import parseString

from meresco.components.sru.sruparser import SruException
from meresco.components.sru import SruHandler, SruParser
from meresco.components.sru.sruhandler import DRILLDOWN_SORTBY_COUNT
from meresco.components.drilldown import SRUTermDrilldown, DRILLDOWN_HEADER, DRILLDOWN_FOOTER, DEFAULT_MAXIMUM_TERMS
from meresco.components.xml_generic.validate import assertValid
from meresco.components.xml_generic import schemasPath
from testhelpers import Response
from meresco.core import Observable

from seecr.test import SeecrTestCase, CallTrace
from seecr.test.io import stderr_replaced

SUCCESS = "SUCCESS"

class SruHandlerTest(SeecrTestCase):

    def testEchoedSearchRetrieveRequest(self):
        sruArguments = {'version':'1.1', 'operation':'searchRetrieve', 'query':'query >= 3', 'recordSchema':'schema', 'recordPacking':'string'}
        component = SruHandler()

        result = "".join(list(component._writeEchoedSearchRetrieveRequest(sruArguments=sruArguments)))
        self.assertEqualsWS("""<srw:echoedSearchRetrieveRequest>
    <srw:version>1.1</srw:version>
    <srw:query>query &gt;= 3</srw:query>
    <srw:recordPacking>string</srw:recordPacking>
    <srw:recordSchema>schema</srw:recordSchema>
</srw:echoedSearchRetrieveRequest>""", result)

    def testEchoedSearchRetrieveRequestWithExtraXParameters(self):
        sruArguments = {'version':'1.1', 'operation':'searchRetrieve', 'query':'query >= 3', 'recordSchema':'schema', 'recordPacking':'string', 'x-link-filter': 'True'}
        component = SruHandler(extraXParameters=['x-link-filter'])

        result = "".join(list(component._writeEchoedSearchRetrieveRequest(sruArguments=sruArguments)))
        self.assertEqualsWS("""<srw:echoedSearchRetrieveRequest>
    <srw:version>1.1</srw:version>
    <srw:query>query &gt;= 3</srw:query>
    <srw:recordPacking>string</srw:recordPacking>
    <srw:recordSchema>schema</srw:recordSchema>
    <srw:x-link-filter>True</srw:x-link-filter>
</srw:echoedSearchRetrieveRequest>""", result)

    def testEchoedSearchRetrieveRequestWithExtraRequestData(self):
        sruArguments = {'version':'1.1', 'operation':'searchRetrieve', 'query':'query >= 3', 'recordSchema':'schema', 'recordPacking':'string', 'x-term-drilldown':['field0,field1']}
        observer = CallTrace('ExtraRequestData')
        observer.methods['echoedExtraRequestData'] = lambda *a, **kw: (x for x in '<some>extra request data</some>')
        component = SruHandler()
        component.addObserver(SRUTermDrilldown())
        component.addObserver(observer)

        result = "".join(list(component._writeEchoedSearchRetrieveRequest(sruArguments=sruArguments)))

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
        drilldownData = [
                {'fieldname': 'field0', 'terms': [{'term': 'value0_0', 'count': 14}]},
                {'fieldname': 'field1', 'terms': [{'term': 'value1_0', 'count': 13}, {'term': 'value1_1', 'count': 11}]},
                {'fieldname': 'field2', 'terms': [{'term': 'value2_0', 'count': 3}, {'term': 'value2_1', 'count': 2}, {'term': 'value2_2', 'count': 1}]}
            ]
        sruHandler.addObserver(sruTermDrilldown)
        result = "".join(sruHandler._writeExtraResponseData(drilldownData=drilldownData, sruArguments={}, **arguments))
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

        component = SruHandler(drilldownSortBy='somevalue')
        component.addObserver(observer)

        queryArguments = dict(startRecord=11, maximumRecords=15, query='query', recordPacking='string', recordSchema='schema')
        sruArguments = queryArguments
        sruArguments['x-term-drilldown'] = ["field0:1,fie:ld1:2,field2,fie:ld3"]
        result = "".join(compose(component.searchRetrieve(sruArguments=sruArguments, **queryArguments)))
        self.assertEquals(['executeQuery'] + ['yieldRecord'] * 15 + ['echoedExtraRequestData', 'extraResponseData'], [m.name for m in observer.calledMethods])
        self.assertEquals([
            dict(fieldname='field0', maxTerms=1, sortBy='somevalue'),
            dict(fieldname='fie:ld1', maxTerms=2, sortBy='somevalue'),
            dict(fieldname='field2', maxTerms=DEFAULT_MAXIMUM_TERMS, sortBy='somevalue'),
            dict(fieldname='fie:ld3', maxTerms=DEFAULT_MAXIMUM_TERMS, sortBy='somevalue')
            ], list(observer.calledMethods[0].kwargs['facets']))
        extraResponseDataMethod = observer.calledMethods[-1]
        self.assertEquals(response, extraResponseDataMethod.kwargs['response'])

    def testNextRecordPosition(self):
        observer = CallTrace(emptyGeneratorMethods=['additionalDiagnosticDetails'])
        response = Response(total=100, hits=hitsRange(11, 26))
        def executeQuery(**kwargs):
            raise StopIteration(response)
            yield
        observer.methods['executeQuery'] = executeQuery
        observer.methods['yieldRecord'] = lambda *a, **kw: (x for x in "record")
        observer.methods['extraResponseData'] = lambda *a, **kw: (x for x in 'extraResponseData')
        observer.methods['echoedExtraRequestData'] = lambda *a, **kw: (x for x in 'echoedExtraRequestData')

        component = SruHandler()
        component.addObserver(observer)

        arguments = dict(startRecord=11, maximumRecords=15, query='query', recordPacking='string', recordSchema='schema')
        result = "".join(compose(component.searchRetrieve(sruArguments=arguments, **arguments)))
        self.assertTrue("<srw:nextRecordPosition>26</srw:nextRecordPosition>" in result, result)

        executeCqlCallKwargs = observer.calledMethods[0].kwargs
        self.assertEquals(10, executeCqlCallKwargs['start']) # SRU is 1 based
        self.assertEquals(25, executeCqlCallKwargs['stop'])

    def testNextRecordPositionNotShownIfAfterLimitBeyond(self):
        observer = CallTrace(emptyGeneratorMethods=['additionalDiagnosticDetails'])
        response = Response(total=100, hits=hitsRange(10, 11))
        def executeQuery(**kwargs):
            raise StopIteration(response)
            yield
        observer.methods['executeQuery'] = executeQuery
        observer.methods['yieldRecord'] = lambda *a, **kw: (x for x in "record")
        observer.methods['extraResponseData'] = lambda *a, **kw: (x for x in 'extraResponseData')
        observer.methods['echoedExtraRequestData'] = lambda *a, **kw: (x for x in 'echoedExtraRequestData')

        component = SruHandler()
        component.addObserver(observer)

        arguments = dict(startRecord=10, maximumRecords=2, query='query', recordPacking='string', recordSchema='schema', limitBeyond=10)
        result = "".join(compose(component.searchRetrieve(sruArguments=arguments, **arguments)))
        self.assertFalse("<srw:nextRecordPosition>" in result, result)

    def testSearchRetrieveVersion11(self):
        queryArguments = {'version':'1.1', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2}
        sruArguments = {'version':'1.1', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2, 'x-recordSchema':['extra', 'evenmore']}

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

        result = "".join(compose(component.searchRetrieve(sruArguments=sruArguments, **queryArguments)))

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
        sruArguments = {'version':'1.2', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2, 'x-recordSchema':['extra', 'evenmore'], 'x-extra-key': 'extraValue'}
        queryArguments = {'version':'1.2', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2}

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

        result = "".join(compose(component.searchRetrieve(sruArguments=sruArguments, **queryArguments)))
        self.assertEquals(['executeQuery', 'echoedExtraRequestData', 'extraResponseData'], [m.name for m in observer.calledMethods])
        executeQueryMethod, echoedExtraRequestDataMethod, extraResponseDataMethod = observer.calledMethods
        self.assertEquals('executeQuery', executeQueryMethod.name)
        methodKwargs = executeQueryMethod.kwargs
        self.assertEquals(parseString('field=value'), methodKwargs['cqlAbstractSyntaxTree'])
        self.assertEquals(0, methodKwargs['start'])
        self.assertEquals(2, methodKwargs['stop'])
        self.assertEquals(0, methodKwargs['suggestionsCount'])
        self.assertEquals({'x-recordSchema': ['extra', 'evenmore'], 'x-extra-key': 'extraValue'}, methodKwargs['extraArguments'])

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
        self.assertEquals(set(['version', 'recordSchema', 'x-recordSchema', 'maximumRecords', 'startRecord', 'query', 'operation', 'recordPacking', 'x-extra-key']), set(echoedExtraRequestDataMethod.kwargs['sruArguments'].keys()))
        self.assertEquals((), extraResponseDataMethod.args)
        self.assertEquals(sorted(['version', 'recordSchema', 'maximumRecords', 'startRecord', 'query', 'operation', 'recordPacking', 'cqlAbstractSyntaxTree', 'response', 'drilldownData', 'queryTime', 'suggestionsQuery', 'sruArguments']), sorted(extraResponseDataMethod.kwargs.keys()))

    def testExtraRecordDataOldStyle(self):
        queryArguments = {'version':'1.2', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2}
        sruArguments = {'version':'1.2', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2, 'x-recordSchema':['extra', 'evenmore']}

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

        result = "".join(compose(component.searchRetrieve(sruArguments=sruArguments, **queryArguments)))

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
        observer = CallTrace(emptyGeneratorMethods=['additionalDiagnosticDetails'])
        observer.exceptions["yieldRecord"] = IOError()
        component = SruHandler()
        component.addObserver(observer)
        result = "".join(list(compose(component._writeRecordData(recordPacking="string", recordSchema="schema", recordId="ID"))))
        self.assertTrue("<uri>info://srw/diagnostics/1/1</uri>" in result)
        self.assertTrue("<message>General System Error</message>" in result)
        self.assertTrue("<details>recordSchema 'schema' for identifier 'ID' does not exist</details>" in result)

    def testExceptionInWriteRecordData(self):
        observer = CallTrace(emptyGeneratorMethods=['additionalDiagnosticDetails'])
        observer.exceptions["yieldRecord"] = Exception("Test Exception")
        component = SruHandler()
        component.addObserver(observer)
        result = "".join(list(compose(component._writeRecordData(recordPacking="string", recordSchema="schema", recordId="ID"))))
        self.assertTrue("<uri>info://srw/diagnostics/1/1</uri>" in result)
        self.assertTrue("<message>General System Error</message>" in result)
        self.assertTrue("<details>Test Exception</details>" in result)

    def testExceptionInWriteExtraRecordData(self):
        class RaisesException(object):
            def extraResponseData(self, *args, **kwargs):
                raise Exception("Test Exception")
        component = SruHandler()
        component.addObserver(RaisesException())
        result = "".join(compose(component._writeExtraResponseData(cqlAbstractSyntaxTree=None)))
        self.assertTrue("<uri>info://srw/diagnostics/1/1</uri>" in result)
        self.assertTrue("<message>General System Error</message>" in result)
        self.assertTrue("<details>Test Exception</details>" in result)

    def testDiagnosticOnExecuteCql(self):
        with stderr_replaced():
            class RaisesException(object):
                def executeQuery(self, *args, **kwargs):
                    raise Exception("Test Exception")
            component = SruHandler()
            component.addObserver(RaisesException())
            arguments = dict(startRecord=11, maximumRecords=15, query='query', recordPacking='string', recordSchema='schema')
            result = parse(StringIO("".join(compose(component.searchRetrieve(sruArguments=arguments, **arguments)))))
            namespaces = {'diag': 'http://www.loc.gov/zing/srw/diagnostic/'}
            diagnostic = result.xpath("//diag:diagnostic", namespaces=namespaces)
            self.assertEquals(1, len(diagnostic))
            self.assertEquals(["info://srw/diagnostics/1/48"], diagnostic[0].xpath("diag:uri/text()", namespaces=namespaces))
            self.assertEquals(["Query Feature Unsupported"], diagnostic[0].xpath("diag:message/text()", namespaces=namespaces))
            self.assertEquals(["Test Exception"], diagnostic[0].xpath("diag:details/text()", namespaces=namespaces))

    def testDiagnosticWarning(self):
        sruArguments = {'version':'1.2', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2, }
        queryArguments = {'version':'1.2', 'operation':'searchRetrieve',  'recordSchema':'schema', 'recordPacking':'xml', 'query':'field=value', 'startRecord':1, 'maximumRecords':2}

        observer = CallTrace(emptyGeneratorMethods=['additionalDiagnosticDetails'])
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

        result = "".join(compose(component.searchRetrieve(sruArguments=sruArguments, diagnostics=[(998, 'Diagnostic 998', 'The <tag> message'), (999, 'Diagnostic 999', 'Some message')], **queryArguments)))

        response = parse(StringIO(result))

        self.assertEquals([t % namespaces for t in [
                '{%(srw)s}version',
                '{%(srw)s}numberOfRecords',
                '{%(srw)s}records',
                '{%(srw)s}nextRecordPosition',
                '{%(srw)s}echoedSearchRetrieveRequest',
                '{%(srw)s}diagnostics',
                '{%(srw)s}extraResponseData',
            ]], [t.tag for t in xpath(response, '//srw:searchRetrieveResponse/*')])

        diagnostics = [{'uri': xpath(d, 'diag:uri/text()')[0],
            'details': xpath(d, 'diag:details/text()')[0],
            'message': xpath(d, 'diag:message/text()')[0]} for d in
                xpath(response, '/srw:searchRetrieveResponse/srw:diagnostics/diag:diagnostic')]
        self.assertEquals([
            {'uri': 'info://srw/diagnostics/1/998', 'message': 'Diagnostic 998', 'details': 'The <tag> message'},
            {'uri': 'info://srw/diagnostics/1/999', 'message': 'Diagnostic 999', 'details': 'Some message'},
            ], diagnostics)


    def testSearchRetrieveAssertsDrilldownMaximumMaximumResultsWhenSet(self):
        drilldownMaximumMaximumResults = 3
        self.assertTrue(drilldownMaximumMaximumResults < DEFAULT_MAXIMUM_TERMS)

        def sruHandlerKwargs(x_term_drilldown):
            arguments = {'version':'1.1', 'operation':'searchRetrieve', 'query':'blissfully_ignored', 'recordSchema':'blissfully_ignored', 'recordPacking':'string'}
            arguments['x_term_drilldown'] = [x_term_drilldown]
            arguments['sruArguments'] = dict((k.replace('_', '-'),v) for k,v in arguments.items())
            return arguments

        # No problem - max
        kwargs = sruHandlerKwargs(x_term_drilldown='field0:3,fielddefault')
        sruHandler = SruHandler(drilldownMaximumMaximumResults=drilldownMaximumMaximumResults)
        observer = CallTrace('observer')
        sruHandler.addObserver(observer)
        def executeQuery(**kwargs):
            raise KeyboardInterrupt('Ok')
            yield
        observer.methods['executeQuery'] = executeQuery

        try:
            ''.join(compose(sruHandler.searchRetrieve(**kwargs)))
        except KeyboardInterrupt, e:
            self.assertEquals('Ok', str(e))
        else:
            self.fail('Should not come here')

        self.assertEquals(['executeQuery'], observer.calledMethodNames())
        self.assertEquals([
                dict(fieldname='field0', maxTerms=3, sortBy=DRILLDOWN_SORTBY_COUNT),
                dict(fieldname='fielddefault', maxTerms=3, sortBy=DRILLDOWN_SORTBY_COUNT)
            ], observer.calledMethods[0].kwargs['facets'])

        # No problem - min
        kwargs = sruHandlerKwargs(x_term_drilldown='field0:1')
        observer.calledMethods.reset()
        try:
            ''.join(compose(sruHandler.searchRetrieve(**kwargs)))
        except KeyboardInterrupt, e:
            self.assertEquals('Ok', str(e))
        else:
            self.fail('Should not come here')

        self.assertEquals(['executeQuery'], observer.calledMethodNames())
        self.assertEquals([dict(fieldname='field0', maxTerms=1, sortBy=DRILLDOWN_SORTBY_COUNT)], observer.calledMethods[0].kwargs['facets'])

        # Too high
        kwargs = sruHandlerKwargs(x_term_drilldown='field0:4')

        sruHandler = SruHandler(drilldownMaximumMaximumResults=drilldownMaximumMaximumResults)
        observer = CallTrace('observer')
        sruHandler.addObserver(observer)
        def executeQuery(**kwargs):
            raise KeyboardInterrupt('Should have failed before triggering this exception!')
            yield
        observer.methods['executeQuery'] = executeQuery

        try:
            ''.join(compose(sruHandler.searchRetrieve(**kwargs)))
        except SruException, e:
            self.assertEquals('field0; drilldown with maximumResults > 3', str(e))
        except KeyboardInterrupt, e:
            self.fail(str(e))
        else:
            self.fail('Should not come here')

        # Too low
        kwargs = sruHandlerKwargs(x_term_drilldown='field55:0')
        try:
            ''.join(compose(sruHandler.searchRetrieve(**kwargs)))
        except SruException, e:
            self.assertEquals('field55; drilldown with maximumResults < 1', str(e))
        except KeyboardInterrupt, e:
            self.fail(str(e))
        else:
            self.fail('Should not come here')

        # Freezing
        kwargs = sruHandlerKwargs(x_term_drilldown='field55:-1')
        try:
            ''.join(compose(sruHandler.searchRetrieve(**kwargs)))
        except SruException, e:
            self.assertEquals('field55; drilldown with maximumResults < 1', str(e))
        except KeyboardInterrupt, e:
            self.fail(str(e))
        else:
            self.fail('Should not come here')

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
        arguments = dict(startRecord=11, maximumRecords=15, query='query', recordPacking='string', recordSchema='schema')
        result = "".join(compose(handler.searchRetrieve(sruArguments=arguments, **arguments)))
        sruResponse = parse(StringIO(result))
        extraResponseData = sruResponse.xpath('/srw:searchRetrieveResponse/srw:extraResponseData', namespaces={'srw':"http://www.loc.gov/zing/srw/"})[0]
        self.assertEqualsWS("""<srw:extraResponseData xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/">
        <querytimes xmlns="http://meresco.org/namespace/timing">
            <sru>PT1.500S</sru>
            <index>PT0.005S</index>
        </querytimes>
</srw:extraResponseData>""", lxmltostring(extraResponseData))
        queryTimes = lxmltostring(extraResponseData.xpath('//ti:querytimes', namespaces={'ti':"http://meresco.org/namespace/timing"})[0])
        assertValid(queryTimes, join(schemasPath, 'timing-20120827.xsd'))

    def testTestXsdEqualsPublishedXsd(self):
        xsd = urlopen("http://meresco.org/files/xsd/timing-20120827.xsd").read()
        localxsd = open(join(schemasPath, 'timing-20120827.xsd')).read()
        self.assertEqualsWS(xsd, localxsd)


    def testDiagnosticGetHandledByObserver(self):
        def mockAdditionalDiagnosticDetails(**kwargs):
            yield "additional details"
        def mockExecuteQuery(*args, **kwargs):
            raise Exception("Zo maar iets")
            yield

        observer = CallTrace(methods={
            'additionalDiagnosticDetails': mockAdditionalDiagnosticDetails,
            'executeQuery': mockExecuteQuery})


        dna = be(
            (Observable(),
                (SruHandler(),
                    (observer, )
                )
            )
        )

        with stderr_replaced():
            response = ''.join(compose(dna.all.searchRetrieve(query="word", sruArguments={})))
            self.assertEquals(['executeQuery', 'additionalDiagnosticDetails'], observer.calledMethodNames())
            self.assertTrue("<details>Zo maar iets - additional details</details>" in response, response)


    def testParseDrilldownArguments(self):
        handler = SruHandler(drilldownSortBy='count')
        self.assertEquals(None, handler._parseDrilldownArgs([]))
        self.assertEquals([], handler._parseDrilldownArgs(['']))
        self.assertEquals([{'fieldname':'field', 'maxTerms':10, 'sortBy':'count'}], handler._parseDrilldownArgs(['field']))
        self.assertEquals([{'fieldname':'field', 'maxTerms':10, 'sortBy':'count'}], handler._parseDrilldownArgs(['field,']))
        self.assertEquals([{'fieldname':'field', 'maxTerms':20, 'sortBy':'count'}], handler._parseDrilldownArgs(['field:20']))
        self.assertEquals([{'fieldname':'field', 'maxTerms':20, 'sortBy':'count'}, {'fieldname':'field2', 'maxTerms':10, 'sortBy':'count'}], handler._parseDrilldownArgs(['field:20,field2']))
        self.assertEquals([[{'fieldname':'field', 'maxTerms':20, 'sortBy':'count'}, {'fieldname':'field2', 'maxTerms':10, 'sortBy':'count'}]], handler._parseDrilldownArgs(['field:20/field2']))
        self.assertEquals([[{'fieldname':'field', 'maxTerms':20, 'sortBy':'count'}, {'fieldname':'field2', 'maxTerms':10, 'sortBy':'count'}],{'fieldname':'field3', 'maxTerms':10, 'sortBy':'count'}], handler._parseDrilldownArgs(['field:20/field2,field3']))
        self.assertEquals([{'fieldname':'field', 'maxTerms':20, 'sortBy':'count'}, {'fieldname':'field2', 'maxTerms':10, 'sortBy':'count'}], handler._parseDrilldownArgs(['field:20','field2']))


def xpath(lxmlNode, path):
    return lxmlNode.xpath(path, namespaces=namespaces)

namespaces = {
        'ti': "http://meresco.org/namespace/timing",
        'srw': "http://www.loc.gov/zing/srw/",
        'diag': "http://www.loc.gov/zing/srw/diagnostic/",
    }
def hitsRange(*args):
    return ['%s' % i for i in range(*args)]
