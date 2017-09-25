#-*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015-2016 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015-2017 Seecr (Seek You Too B.V.) http://seecr.nl
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
from simplejson import loads
from urlparse import urlparse, parse_qs
from urllib import urlencode
from collections import namedtuple, OrderedDict
from cqlparser import cqlToExpression
from cqlparser.cqltoexpression import QueryExpression

from meresco.components.search import JsonSearch

class JsonSearchTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        ts = [(1 + i*0.1) for i in xrange(100)]
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
            raise StopIteration(result)
            yield

        def retrieveData(identifier, name):
            raise StopIteration({'identifier':identifier, 'name': name})
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
        self.assertEquals(['executeQuery', 'retrieveData', 'retrieveData'], self.observer.calledMethodNames())
        self.assertEquals(['response', 'request', 'version'], json.keys())
        self.assertEquals(2, len(json['response']['items']))
        self.assertEquals(2, json['response']['total'])

        record_1 = json['response']['items'][0]
        self.assertEquals({'identifier': 'id:1', 'name': 'rdf'}, record_1)
        record_2 = json['response']['items'][1]
        self.assertEquals({'identifier': 'id:2', 'name': 'rdf'}, record_2)

    def testTimes(self):
        json = self.request()
        self.assertEquals({
            'handlingTime': 0.2,
            'indexTime': 0.03,
            'queryTime': 0.1
            }, json['response']['querytimes'])

    def testQuery(self):
        self.request()
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEquals(QueryExpression.searchterm(term='*'), executeQueryMethod.kwargs['query'])
        self.assertEquals({'original': {'query': '*'}}, executeQueryMethod.kwargs['extraArguments'])

    def testQueryNotCQLButWebQueryStyle(self):
        self.request(query="fiets water")
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEquals(cqlToExpression("fiets AND water"), executeQueryMethod.kwargs['query'])
        self.assertEquals({'original': {'query': 'fiets AND water'}}, executeQueryMethod.kwargs['extraArguments'])

    def testPage0(self):
        json = self.request()
        self.assertEquals(2, json['response']['total'])
        self.assertEquals(2, len(json['response']['items']))
        self.assertFalse('next' in json['response'])
        self.assertFalse('previous' in json['response'])

    def testPage1(self):
        self.hits.extend(range(3,11))
        self.total = 30
        json = self.request()
        self.assertEquals(30, json['response']['total'])
        self.assertEquals(10, len(json['response']['items']))
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEquals(0, executeQueryMethod.kwargs['start'])
        self.assertEquals(10, executeQueryMethod.kwargs['stop'])
        self.assertEquals(2, json['response']['next']['page'])
        self.assertFalse('previous' in json['response'])

    def testPage2(self):
        del self.hits[:]
        self.hits.extend(range(11,21))
        self.total = 30
        json = self.request(page="2")
        self.assertEquals(30, json['response']['total'])
        self.assertEquals(10, len(json['response']['items']))
        self.assertEquals("id:11", json['response']['items'][0]['identifier'])
        self.assertEquals(2, json['request']['page'])
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEquals(10, executeQueryMethod.kwargs['start'])
        self.assertEquals(20, executeQueryMethod.kwargs['stop'])
        nextLink = self.parseLink(json['response']['next']['link'])
        self.assertEquals(3, json['response']['next']['page'])
        self.assertEquals({'page': ['3'], 'query': ['*']}, nextLink.query)
        self.assertEquals(1, json['response']['previous']['page'])

    def testPage3(self):
        del self.hits[:]
        self.hits.extend(range(21,31))
        self.total = 30
        json = self.request(page="3")
        self.assertEquals(30, json['response']['total'])
        self.assertEquals(10, len(json['response']['items']))
        self.assertEquals("id:21", json['response']['items'][0]['identifier'])
        self.assertEquals(3, json['request']['page'])
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEquals(20, executeQueryMethod.kwargs['start'])
        self.assertEquals(30, executeQueryMethod.kwargs['stop'])
        self.assertFalse('next' in json['response'])
        self.assertEquals(2, json['response']['previous']['page'])

    def testPageSize0(self):
        del self.hits[:]
        json = self.request(pageSize="0")
        self.assertEquals(2, json['response']['total'])
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEquals(0, executeQueryMethod.kwargs['start'])
        self.assertEquals(0, executeQueryMethod.kwargs['stop'])
        self.assertFalse('items' in json['response'])
        self.assertFalse('next' in json['response'])
        self.assertFalse('previous' in json['response'])

    def testPageSize1(self):
        json = self.request(pageSize="1")
        self.assertEquals(2, json['response']['total'])
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEquals(0, executeQueryMethod.kwargs['start'])
        self.assertEquals(1, executeQueryMethod.kwargs['stop'])
        self.assertEquals({
                'link': '/search?page=2&pageSize=1&query=%2A',
                'page': 2,
            }, json['response']['next'])
        self.assertFalse('previous' in json['response'])
        self.assertEquals(1, json['request']['pageSize'])

    def testPageSize2(self):
        json = self.request(pageSize="1", page="2")
        self.assertEquals(2, json['response']['total'])
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEquals(1, executeQueryMethod.kwargs['start'])
        self.assertEquals(2, executeQueryMethod.kwargs['stop'])
        self.assertEquals({
                'link': '/search?page=1&pageSize=1&query=%2A',
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
        self.assertEquals([{
                'fieldname': 'field',
                'maxTerms': 100,
                'sortBy': 'count',
            }], executeQueryMethod.kwargs['facets'])
        self.assertEquals({
                'field': [
                    {   "count": 23,
                        "value": "value0",
                        "link": "/search?facet=field&facet-filter=field%3Dvalue0&query=%2A",
                    },
                    {   "count": 4,
                        "value": "value1",
                        "link": "/search?facet=field&facet-filter=field%3Dvalue1&query=%2A",
                    },
                ]
            }, json['response']['facets'])
        nextLink = self.parseLink(json['response']['next']['link'])
        self.assertEquals(['field'], nextLink.query['facet'])
        self.assertEquals(['field'], json['request']['facet'])

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
        self.assertEquals(['executeQuery', 'retrieveData', 'retrieveData', 'labelForUri', 'labelForUri'], self.observer.calledMethodNames())
        self.assertEquals({
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
        json = self.request(facet=['field0', 'field1'])
        nextLink = self.parseLink(json['response']['next']['link'])
        self.assertEquals(['field0', 'field1'], nextLink.query['facet'])
        self.assertEquals(['field0', 'field1'], json['request']['facet'])
        self.assertEquals(set(['field0', 'field1']),
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
        self.assertEquals(['executeQuery', 'retrieveData', 'retrieveData'], self.observer.calledMethodNames())
        self.assertEquals({
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
        self.assertEquals(['field=somevalue', 'field=value0'], link.query['facet-filter'])

    def testPassXArguments(self):
        self.request(**{'x-disable-filter': 'encyclopedie', 'x-something-else': 'important'})
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEquals({
                'original': {'query': '*'},
                'x-disable-filter': ['encyclopedie'],
                'x-something-else': ['important'],
            }, executeQueryMethod.kwargs['extraArguments'])


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
        self.assertEquals(['field=value0'], link.query['facet-filter'])

    def testFacetFilters(self):
        self.request(facet='field', **{'facet-filter': ['field0=value0', 'field1=value1']})
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEquals(cqlToExpression('* AND field0 exact value0 AND field1 exact value1'), executeQueryMethod.kwargs['query'])

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


    def testTODO(self):
        pass
        # ERROR tests op verschillende stukken.
        # maximum number of records.
        # ERROR query geen CQL query
        # use full path for link etc.

    def testSequenceOfKeys(self):
        self.total = 500
        self.hits = xrange(10)
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
        self.assertEqual(['response', 'request', 'version'], json.keys())
        self.assertEqual(['total', 'items', 'facets', 'querytimes', 'next', 'previous'], json['response'].keys())

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
        arguments = parse_qs(urlencode(arguments, doseq=True))
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
        for k,v in attrs.items():
            setattr(self, k, v)
