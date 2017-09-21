#-*- coding: utf-8 -*-
## begin license ##
#
# Drents Archief beoogt het Drents erfgoed centraal beschikbaar te stellen.
#
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015-2016 Drents Archief http://www.drentsarchief.nl
#
# This file is part of "Drents Archief"
#
# "Drents Archief" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Drents Archief" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Drents Archief"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from meresco.components.json import JsonDict
from meresco.components.log import collectLogForScope
from meresco.components.sru.sruhandler import DRILLDOWN_SORTBY_COUNT
from meresco.components.web import WebQuery
from meresco.core import Observable
from cqlparser import cqlToExpression
from simplejson import dumps
from urllib import urlencode as _urlencode

from meresco.components.http.utils import CRLF

from decimal import Decimal
from time import time
from simplejson import dumps

first={key:nr for nr, key in enumerate(reversed(['total', 'items']), start=1)}
last={key:nr for nr, key in enumerate(['next', 'previous', 'version'], start=1)}
def item_sort_key((k,v)):
    return ' '*first.get(k,0) + chr(127)*last.get(k,0) + k

class JsonSearch(Observable):
    VERSION = 0.1

    def __init__(self, defaultRecordSchema, pageSize=10, maximumRecordNumber=1000, **kwargs):
        Observable.__init__(self, **kwargs)
        self._defaultRecordSchema = defaultRecordSchema
        self._pageSize = pageSize
        self._maximumRecordNumber = maximumRecordNumber

    def handleRequest(self, path, arguments, *args, **kwargs):
        logDict = dict()
        try:
            jsonResult = JsonDict({
                'version': self.VERSION,
            })
            request = self.parseArgs(path, arguments)

            jsonResult.setdefault('request', dict(request.queryDict))

            jsonResponse = yield self.jsonResponse(**request.queryKwargs)
            if request.pageSize and jsonResponse["total"] > request.stop:
                jsonResponse['next'] = self.pageDict(1, request, path=path)
            if request.pageSize and request.start > 0:
                jsonResponse['previous'] = self.pageDict(-1, request, path=path)

            for fieldname, terms in jsonResponse.get('facets', {}).items():
                fieldList = [
                    self.facetDict(path, request, fieldname=fieldname, term=term)
                    for term in terms
                ]
                jsonResponse['facets'][fieldname] = fieldList
            jsonResult['response'] = jsonResponse

            yield "HTTP/1.0 200 OK" + CRLF
            yield "Content-type: application/json" + CRLF
            yield CRLF
            yield dumps(jsonResult, item_sort_key=item_sort_key, indent=2)
        finally:
            collectLogForScope(search=logDict)

    def jsonResponse(self, **kwargs):
        t0 = self._timeNow()
        result = yield self.any.executeQuery(**kwargs)

        queryTime = self._timeNow() - t0
        total, hits = result.total, result.hits
        jsonResponse = JsonDict({'total': total})

        if hits:
            if hasattr(result, 'items'):
                jsonResponse['items'] = result.items
            else:
                jsonResponse['items'] = []
                for hit in hits:
                    jsonResponse['items'].append((yield self.any.retrieveData(hit.id, self._defaultRecordSchema)))

        drilldownData = getattr(result, 'drilldownData', None)
        if drilldownData is not None:
            jsonFacets = jsonResponse.setdefault('facets', {})
            for facet in drilldownData:
                jsonFacets.setdefault(facet['fieldname'], facet["terms"])

        searchTime = self._timeNow() - t0
        jsonResponse['querytimes'] = {
            'handlingTime': self._querytime(searchTime),
            'queryTime': self._querytime(queryTime),
        }
        if result.queryTime:
            jsonResponse["querytimes"]["indexTime"] = self._querytime(result.queryTime/1000.0)

        raise StopIteration(jsonResponse)

    def facetDict(self, path, request, fieldname, term):
        termDict = dict(request.queryDict)
        facetFilter = set(termDict.get('facet-filter', []))
        facetFilter.add("{0}={1}".format(fieldname, term['term']))
        termDict['facet-filter'] = list(facetFilter)
        result = dict(
            count=term['count'],
            value=term['term'],
            link="{0}?{1}".format(path, urlencode(sorted(termDict.items())))
        )
        if fieldname.endswith('.uri'):
            displayValue = term['displayTerm'] if 'displayTerm' in term else self.call.labelForUri(uri=term['term'])
            if displayValue:
                result['displayValue'] = displayValue
        return result

    def parseArgs(self, path, arguments):
        query = arguments['query'][0]
        query = WebQuery(query).asString()
        page = int(arguments.get('page', ["1"])[0])
        pageSize = int(arguments.get('pageSize', [self._pageSize])[0])
        start = (page - 1) * pageSize
        stop = start + pageSize
        facets = arguments.get('facet', [])
        facetFilters = arguments.get('facet-filter', [])
        queryFacets = []
        for facet in facets:
            fieldname, maxTerms = facet, 30
            splitted = facet.rsplit(':', 1)
            try:
                maxTerms = int(splitted[1]) if len(splitted) > 1 else 10
                fieldname = splitted[0]
            except ValueError:
                pass
            queryFacets.append(dict(fieldname=fieldname, maxTerms=maxTerms, sortBy=DRILLDOWN_SORTBY_COUNT))
        queryKwargs=dict(
                start=start,
                stop=stop,
                query=cqlToExpression(query),
                extraArguments={"original":{'query':query}},
                facets=queryFacets or None,
            )
        for k, v in arguments.items():
            if k.startswith('x-'):
                queryKwargs['extraArguments'][k] = v
        queryDict=dict(query=query)
        if page != 1:
            queryDict['page'] = page
        if pageSize != self._pageSize:
            queryDict['pageSize'] = pageSize
        if facets:
            queryDict['facet'] = [qf["fieldname"] for qf in queryFacets]
        if facetFilters:
            queryDict['facet-filter'] = facetFilters
            queryKwargs['extraArguments']['x-drilldown-query'] = facetFilters
        return MyDict(
            page=page,
            pageSize=pageSize,
            query=query,
            stop=stop,
            start=start,
            queryKwargs=queryKwargs,
            queryDict=queryDict,
        )

    def pageDict(self, pageAdditon, request, path):
        linkDict = dict(request.queryDict)
        response = {'page': request.page + pageAdditon}
        linkDict.update(response)
        response['link'] = '{0}?{1}'.format(
                path,
                urlencode(sorted(linkDict.items()))
            )
        return response

    def _timeNow(self):
        return time()

    def _querytime(self, t):
        return Decimal(t).quantize(MILLIS)

class MyDict(dict):
    def __getattr__(self, key):
        return self[key]

urlencode = lambda arg: _urlencode(arg, doseq=True)

RESOURCE_RELATIONS = set([
    'edm:isShownAt',
    'edm:isShownBy',
])

TYPES_TO_IGNORE = set(['oa:Annotation'])
MILLIS = Decimal('0.001')
