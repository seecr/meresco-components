#-*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015-2016 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015-2017, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from weightless.core import be, asString, local
from meresco.components import lxmltostring
from meresco.components.http.utils import CRLF
from meresco.components.log import LogCollectorScope, LogCollector
from meresco.core import Observable
from meresco.xml.namespaces import namespaces
from meresco.xml.utils import createElement, createSubElement
from json import loads
from urllib.parse import urlparse, parse_qs
from urllib.parse import urlencode
from collections import namedtuple, OrderedDict
from cqlparser import cqlToExpression
from cqlparser.cqltoexpression import QueryExpression

from meresco.components.search import JsonSearch

class JsonSearchTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        ts = [(1 + i*0.1) for i in range(100)]
        def timeNow():
            return ts.pop(0)
        self._timeNow = timeNow
        class MockHit(object):
            def __init__(self, id):
                self.id = id
        self.total = 2
        self.hits = [1,2]
        self.drilldownData = None

        def executeQuery(*args, **kwargs):
            result = LuceneResponse(
                    total=self.total,
                    hits=[MockHit('id:%s' % i) for i in self.hits],
                    queryTime=30
                )
            if self.drilldownData:
                result.drilldownData = self.drilldownData
            return result
            yield

        def retrieveData(identifier, name):
            return {'identifier':identifier, 'name': name}
            yield

        self.observer = CallTrace(methods=dict(
            executeQuery=executeQuery,
            retrieveData=retrieveData))
        self._buildDna()

    def _buildDna(self, defaultRecordSchema="rdf", **kwargs):
        jsonSearch = JsonSearch(defaultRecordSchema=defaultRecordSchema, **kwargs)
        jsonSearch._timeNow = self._timeNow

        self.dna = be(
            (Observable(),
                (LogCollector(),
                    (jsonSearch,
                        (self.observer, )
                    )
                )
            )
        )

    def testRecords(self):
        json = self.request()
        self.assertEqual(['executeQuery', 'retrieveData', 'retrieveData'], self.observer.calledMethodNames())
        self.assertEqual(['response', 'request', 'version'], list(json.keys()))
        self.assertEqual(2, len(json['response']['items']))
        self.assertEqual(2, json['response']['total'])

        record_1 = json['response']['items'][0]
        self.assertEqual({'identifier': 'id:1', 'name': 'rdf'}, record_1)
        record_2 = json['response']['items'][1]
        self.assertEqual({'identifier': 'id:2', 'name': 'rdf'}, record_2)

    def testRecordSchema(self):
        json = self.request(recordSchema='recordSchema')
        self.assertEqual(['executeQuery', 'retrieveData', 'retrieveData'], self.observer.calledMethodNames())
        self.assertEqual(['response', 'request', 'version'], list(json.keys()))
        self.assertEqual(2, len(json['response']['items']))
        self.assertEqual(2, json['response']['total'])

        record_1 = json['response']['items'][0]
        self.assertEqual({'identifier': 'id:1', 'name': 'recordSchema'}, record_1)

    def testTimes(self):
        json = self.request()
        self.assertEqual({
            'handlingTime': 0.2,
            'indexTime': 0.03,
            'queryTime': 0.1
            }, json['response']['querytimes'])

    def testQuery(self):
        self.request()
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual(QueryExpression.searchterm(term='*'), executeQueryMethod.kwargs['query'])

    def testQueryNotCQLButWebQueryStyle(self):
        self.request(query="fiets water")
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual(cqlToExpression("fiets AND water"), executeQueryMethod.kwargs['query'])

    def testPage0(self):
        json = self.request()
        self.assertEqual(2, json['response']['total'])
        self.assertEqual(2, len(json['response']['items']))
        self.assertFalse('next' in json['response'])
        self.assertFalse('previous' in json['response'])

    def testPage1(self):
        self.hits.extend(list(range(3,11)))
        self.total = 30
        json = self.request()
        self.assertEqual(30, json['response']['total'])
        self.assertEqual(10, len(json['response']['items']))
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual(0, executeQueryMethod.kwargs['start'])
        self.assertEqual(10, executeQueryMethod.kwargs['stop'])
        self.assertEqual(2, json['response']['next']['page'])
        self.assertFalse('previous' in json['response'])

    def testPage2(self):
        del self.hits[:]
        self.hits.extend(list(range(11,21)))
        self.total = 30
        json = self.request(page="2")
        self.assertEqual(30, json['response']['total'])
        self.assertEqual(10, len(json['response']['items']))
        self.assertEqual("id:11", json['response']['items'][0]['identifier'])
        self.assertEqual(2, json['request']['page'])
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual(10, executeQueryMethod.kwargs['start'])
        self.assertEqual(20, executeQueryMethod.kwargs['stop'])
        nextLink = self.parseLink(json['response']['next']['link'])
        self.assertEqual(3, json['response']['next']['page'])
        self.assertEqual({'page': ['3'], 'query': ['*']}, nextLink.query)
        self.assertEqual(1, json['response']['previous']['page'])

    def testPage3(self):
        del self.hits[:]
        self.hits.extend(list(range(21,31)))
        self.total = 30
        json = self.request(page="3")
        self.assertEqual(30, json['response']['total'])
        self.assertEqual(10, len(json['response']['items']))
        self.assertEqual("id:21", json['response']['items'][0]['identifier'])
        self.assertEqual(3, json['request']['page'])
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual(20, executeQueryMethod.kwargs['start'])
        self.assertEqual(30, executeQueryMethod.kwargs['stop'])
        self.assertFalse('next' in json['response'])
        self.assertEqual(2, json['response']['previous']['page'])

    def testPageSize0(self):
        del self.hits[:]
        json = self.request(**{'page-size':"0"})
        self.assertEqual(2, json['response']['total'])
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual(0, executeQueryMethod.kwargs['start'])
        self.assertEqual(0, executeQueryMethod.kwargs['stop'])
        self.assertFalse('items' in json['response'])
        self.assertFalse('next' in json['response'])
        self.assertFalse('previous' in json['response'])

    def testPageSize1(self):
        json = self.request(**{'page-size':"1"})
        self.assertEqual(2, json['response']['total'])
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual(0, executeQueryMethod.kwargs['start'])
        self.assertEqual(1, executeQueryMethod.kwargs['stop'])
        self.assertEqual({
                'link': '/search?page=2&page-size=1&query=%2A',
                'page': 2,
            }, json['response']['next'])
        self.assertFalse('previous' in json['response'])
        self.assertEqual(1, json['request']['page-size'])

    def testPageSize2(self):
        json = self.request(page="2", **{'page-size':'1'})
        self.assertEqual(2, json['response']['total'])
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual(1, executeQueryMethod.kwargs['start'])
        self.assertEqual(2, executeQueryMethod.kwargs['stop'])
        self.assertEqual({
                'link': '/search?page=1&page-size=1&query=%2A',
                'page': 1,
            }, json['response']['previous'])
        self.assertFalse('next' in json['response'])

    def testNoFacet(self):
        json = self.request()
        self.assertFalse('facets' in json['response'])

    def testFacet(self):
        self.total = 30
        self.drilldownData = [{
                "fieldname": "field",
                "path": [],
                "terms": [
                    {   "count": 23,
                        "term": "value0"
                    },
                    {   "count": 4,
                        "term": "value1"
                    }
                ]
            },
        ]
        json = self.request(facet='field:100')
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual([{
                'fieldname': 'field',
                'maxTerms': 100,
                'sortBy': 'count',
            }], executeQueryMethod.kwargs['facets'])
        self.assertEqual({
                'field': [
                    {   "count": 23,
                        "value": "value0",
                        "link": "/search?facet=field%3A100&facet-filter=field%3Dvalue0&query=%2A",
                    },
                    {   "count": 4,
                        "value": "value1",
                        "link": "/search?facet=field%3A100&facet-filter=field%3Dvalue1&query=%2A",
                    },
                ]
            }, json['response']['facets'])
        nextLink = self.parseLink(json['response']['next']['link'])
        self.assertEqual(['field:100'], nextLink.query['facet'])
        self.assertEqual([{'index':'field', 'max-terms':100}], json['request']['facet'])

    def testFacetDisplayValue(self):
        self.total = 30
        self.drilldownData = [{
                "fieldname": "field:test.uri",
                "path": [],
                "terms": [
                    {   "count": 23,
                        "term": "value0"
                    },
                    {   "count": 4,
                        "term": "value1"
                    }
                ]
            },
        ]
        def labelForUri(uri):
            return {'value0':'Waarde 0', 'value1': 'Waarde 1'}[uri]
        self.observer.methods['labelForUri'] = labelForUri
        json = self.request(facet='field:test.uri')
        self.assertEqual(['executeQuery', 'retrieveData', 'retrieveData', 'labelForUri', 'labelForUri'], self.observer.calledMethodNames())
        self.assertEqual({
                'field:test.uri': [
                    {   "count": 23,
                        "value": "value0",
                        "link": "/search?facet=field%3Atest.uri&facet-filter=field%3Atest.uri%3Dvalue0&query=%2A",
                        "displayValue": "Waarde 0",
                    },
                    {   "count": 4,
                        "value": "value1",
                        "link": "/search?facet=field%3Atest.uri&facet-filter=field%3Atest.uri%3Dvalue1&query=%2A",
                        "displayValue": "Waarde 1",
                    },
                ]
            }, json['response']['facets'])
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual([{'fieldname': 'field:test.uri', 'maxTerms': 10, 'sortBy': 'count'}], executeQueryMethod.kwargs['facets'])


    def testMultipleFacets(self):
        self.total = 30
        self.drilldownData = [
            {   "fieldname": "field0",
                "path": [],
                "terms": [{
                        "count": 23,
                        "term": "value0"
                    },]
            },
            {   "fieldname": "field1",
                "path": [],
                "terms": [{
                        "count": 13,
                        "term": "value0"
                    },]
            },
        ]
        json = self.request(facet=['field0', 'field1:3'])
        nextLink = self.parseLink(json['response']['next']['link'])
        self.assertEqual(['field0', 'field1:3'], nextLink.query['facet'])
        self.assertEqual([{'index':'field0', 'max-terms':10}, {'index':'field1', 'max-terms':3}], json['request']['facet'])
        self.assertEqual(set(['field0', 'field1']),
            set(json['response']['facets'].keys()))

    def testDisplayValueForDisplayTerm(self):
        self.total = 30
        self.drilldownData = [{
                "fieldname": "field:test.uri",
                "path": [],
                "terms": [
                    {   "count": 23,
                        "term": "value0",
                        "displayTerm": "Waarde 0",
                    },
                    {   "count": 4,
                        "term": "value1",
                        "displayTerm": "Waarde 1",
                    }
                ]
            },
        ]
        json = self.request(facet='field:test.uri')
        self.assertEqual(['executeQuery', 'retrieveData', 'retrieveData'], self.observer.calledMethodNames())
        self.assertEqual({
                'field:test.uri': [
                    {   "count": 23,
                        "value": "value0",
                        "link": "/search?facet=field%3Atest.uri&facet-filter=field%3Atest.uri%3Dvalue0&query=%2A",
                        "displayValue": "Waarde 0",
                    },
                    {   "count": 4,
                        "value": "value1",
                        "link": "/search?facet=field%3Atest.uri&facet-filter=field%3Atest.uri%3Dvalue1&query=%2A",
                        "displayValue": "Waarde 1",
                    },
                ]
            }, json['response']['facets'])

    def testFacetFilter(self):
        self.drilldownData = [
            {   "fieldname": "field",
                "path": [],
                "terms": [{
                        "count": 23,
                        "term": "value0"
                    },]
            }
        ]
        json = self.request(facet='field', **{'facet-filter': 'field=somevalue'})
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual(cqlToExpression('* AND field exact somevalue'), executeQueryMethod.kwargs['query'])
        facets = json['response']['facets']
        link = self.parseLink(facets['field'][0]['link'])
        self.assertEqual(sorted(['field=somevalue', 'field=value0']), sorted(link.query['facet-filter']))

    def testPassXArguments(self):
        self.total = 100
        response = self.request(**{'x-disable-filter': 'encyclopedie', 'x-something-else': 'important'})
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual({
                'x-disable-filter': ['encyclopedie'],
                'x-something-else': ['important'],
            }, executeQueryMethod.kwargs['extraArguments'])
        self.assertEqual({'query':['*'],
                'page': ['2'],
                'x-disable-filter': ['encyclopedie'],
                'x-something-else': ['important'],
            }, self.parseLink(response['response']['next']['link']).query)
        self.assertEqual({'query':'*',
                'x-disable-filter': ['encyclopedie'],
                'x-something-else': ['important'],
            }, response['request'])


    def testFacetFilterDoesNotRepeat(self):
        self.drilldownData = [
            {   "fieldname": "field",
                "path": [],
                "terms": [{
                        "count": 23,
                        "term": "value0"
                    },]
            }
        ]
        json = self.request(facet='field', **{'facet-filter': 'field=value0'})
        facets = json['response']['facets']
        link = self.parseLink(facets['field'][0]['link'])
        self.assertEqual(['field=value0'], link.query['facet-filter'])

    def testFacetFilters(self):
        self.request(facet='field', **{'facet-filter': ['field0=value0', 'field1=value1']})
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual(cqlToExpression('* AND field0 exact value0 AND field1 exact value1'), executeQueryMethod.kwargs['query'])

    def testLinksWithOtherPath(self):
        self._buildDna(useOriginalPath=True)
        self.total = 500
        self.drilldownData = [
            {   "fieldname": "field",
                "path": [],
                "terms": [{
                        "count": 23,
                        "term": "value0"
                    },]
            }
        ]
        response = self.request(originalPath='/path/to/search', path='/search', query='*', page=2, facet='field')
        self.assertEqual('/path/to/search', self.parseLink(response['response']['previous']['link']).path)
        self.assertEqual('/path/to/search', self.parseLink(response['response']['next']['link']).path)
        self.assertEqual('/path/to/search', self.parseLink(response['response']['facets']['field'][0]['link']).path)

    def testGetItemsFromObserver(self):
        self._buildDna(getItemsFromObserver=True)
        response = self.request()
        self.assertEqual(['executeQuery', 'getItem', 'getItem'], self.observer.calledMethodNames())
        getItem = self.observer.calledMethods[-1]
        self.assertEqual(dict(identifier='id:2', recordSchema='rdf'), getItem.kwargs)

        self.observer.calledMethods.reset()

        response = self.request(recordSchema='another')
        self.assertEqual(['executeQuery', 'getItem', 'getItem'], self.observer.calledMethodNames())
        getItem = self.observer.calledMethods[-1]
        self.assertEqual(dict(identifier='id:2', recordSchema='another'), getItem.kwargs)

    def testParameterQueryOmitted(self):
        response = self.request(facet='field', query=None)
        self.assertEqual(dict(type="MissingArgument", message="Missing required argument: 'query'"), response['error'])

    def testParameterQueryWebQuery(self):
        response = self.request(query='value1 value2')
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual(cqlToExpression('value1 AND value2'), executeQueryMethod.kwargs['query'])
        self.assertEqual('value1 value2', response['request']['query'])
        self.observer.calledMethods.reset()

        response = self.request(query='-value')
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual(cqlToExpression('* NOT value'), executeQueryMethod.kwargs['query'])
        self.assertEqual('-value', response['request']['query'])

    def testParameterErrorsInPage(self):
        response = self.request(page='0')
        self.assertEqual({
                'type':'InvalidArgument',
                'message':"Invalid argument: 'page', expected value > 0",
            }, response['error'])
        self.assertFalse('response' in response)

        response = self.request(page='q')
        self.assertFalse('response' in response)
        self.assertEqual({
                'type':'InvalidArgument',
                'message':"Invalid argument: 'page', expected integer",
            }, response['error'])

    def testParameterErrorsInPageSize(self):
        response = self.request(**{'page-size':'-1'})
        self.assertEqual({
                'type':'InvalidArgument',
                'message':"Invalid argument: 'page-size', expected value >= 0",
            }, response['error'])
        self.assertFalse('response' in response)

        response = self.request(**{'page-size':'page'})
        self.assertEqual({
                'type':'InvalidArgument',
                'message':"Invalid argument: 'page-size', expected integer",
            }, response['error'])
        self.assertFalse('response' in response)

    def testMaximumNrOfRecords(self):
        response = self.request(**{'page-size': '521', 'page': 3})
        self.assertFalse('response' in response)
        self.assertEqual({
                'type':'InvalidArgument',
                'message':"Invalid argument: 'page', expected value <= 2",
            }, response['error'])
        self.observer.calledMethods.reset()
        response = self.request(**{'page-size': '521', 'page': 2})
        self.assertEqual(1000, self.observer.calledMethods[0].kwargs['stop'])

    def testBadArguments(self):
        response = self.request(unkown_parameter='value')
        self.assertEqual({'type':'BadArgument', 'message':"Bad argument: 'unkown_parameter' is an illegal parameter"}, response['error'])

    def testSequenceOfKeys(self):
        self.total = 500
        self.hits = range(10)
        self.drilldownData = [
            {   "fieldname": "field",
                "path": [],
                "terms": [{
                        "count": 23,
                        "term": "value0"
                    },]
            }
        ]
        json = self.request(page=2, facet='field', **{'facet-filter': 'field=value0'})
        self.assertEqual(['response', 'request', 'version'], list(json.keys()))
        self.assertEqual(['total', 'items', 'facets', 'querytimes', 'next', 'previous'], list(json['response'].keys()))

    def testBadFacetFilter(self):
        response = self.request(**{'facet-filter':'field'})
        self.assertEqual({
                'message': "Invalid argument: 'facet-filter', expected <field>=<value> as a filter",
                'type': 'InvalidArgument',
            }, response['error'])

    ## hellpers

    def request(self, **kwargs):
        requestDict=dict(path=kwargs.pop('path', '/search'))
        originalPath = kwargs.pop('originalPath', None)
        if originalPath is not None:
            requestDict["originalPath"]=originalPath
        arguments = {
            'query': kwargs.pop('query', '*')
        }
        arguments.update(kwargs)
        arguments = parse_qs(urlencode({k:v for k,v in list(arguments.items()) if v is not None}, doseq=True))
        requestDict['arguments'] = arguments
        header, body = asString(self.dna.all.handleRequest(**requestDict)).split(CRLF*2,1)
        json = loads(body, object_pairs_hook=OrderedDict)
        return json

    def parseLink(self, aLink):
        Link = namedtuple('Link', ['path', 'query'])
        r = urlparse(aLink)
        return Link(r.path, parse_qs(r.query))

class LuceneResponse(object):
    def __init__(self, **attrs):
        for k,v in list(attrs.items()):
            setattr(self, k, v)
