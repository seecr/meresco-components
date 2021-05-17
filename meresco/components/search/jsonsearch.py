#-*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015-2016 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015-2018, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2017, 2020 SURF https://www.surf.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
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

from meresco.components.json import JsonDict
from meresco.components.log import collectLogForScope
from meresco.components.sru.sruhandler import DRILLDOWN_SORTBY_COUNT
from meresco.components.web import WebQuery
from meresco.core import Observable
from cqlparser import cqlToExpression
from cqlparser.cqltoexpression import QueryExpression
from simplejson import dumps
from urllib.parse import urlencode as _urlencode

from meresco.components.http.utils import CRLF

from decimal import Decimal
from time import time

class JsonSearch(Observable):
    VERSION = 0.1

    def __init__(self,
            defaultRecordSchema,
            pageSize=10,
            maximumRecordNumber=1000,
            defaultMaxTermsFacet=10,
            useOriginalPath=False,
            getItemsFromObserver=False,
            version=VERSION,
            **kwargs
        ):
        Observable.__init__(self, **kwargs)
        self._version = version
        self._defaultRecordSchema = defaultRecordSchema
        self._pageSize = pageSize
        self._maximumRecordNumber = maximumRecordNumber
        self._defaultMaxTermsFacet = defaultMaxTermsFacet
        self._argumentLimits=dict(
                page_size=pageSize,
                maximum_record_number=maximumRecordNumber,
                default_facet_terms_count=defaultMaxTermsFacet,
                default_record_schema=defaultRecordSchema,
            )
        self._determinePath = lambda **kwargs:kwargs['path']
        if useOriginalPath:
            self._determinePath = lambda **kwargs:kwargs.get('originalPath', kwargs['path'])
        self._getItems = self._observerGetItems if getItemsFromObserver else self._defaultGetItems

    def handleRequest(self, arguments, *args, **kwargs):
        path = self._determinePath(**kwargs)
        logDict = dict()
        jsonResult = {
            'version': self._version,
        }
        try:
            try:
                args = _Arguments(arguments, **self._argumentLimits)

                jsonResult.setdefault('request', args.request)

                jsonResponse = yield self.jsonResponse(args)
                if args.stop - args.start and jsonResponse["total"] > args.stop:
                    jsonResponse['next'] = args.pageDict(1, path=path)
                if args.stop - args.start and args.start > 0:
                    jsonResponse['previous'] = args.pageDict(-1, path=path)

                for fieldname, terms in jsonResponse.get('facets', {}).items():
                    if fieldname.endswith('.uri'):
                        def displayValue(term):
                            return term['displayTerm'] if 'displayTerm' in term else self.call.labelForUri(uri=term['term'])
                    else:
                        displayValue = lambda term: None
                    fieldList = [
                        args.facetDict(path, fieldname=fieldname, term=term, displayValue=displayValue(term))
                        for term in terms
                    ]
                    jsonResponse['facets'][fieldname] = fieldList
                jsonResult['response'] = jsonResponse
            except ValueError as e:
                jsonResult['error'] = {
                        'type': type(e).__name__,
                        'message': str(e),
                    }
            yield "HTTP/1.0 200 OK" + CRLF
            yield "Content-type: application/json" + CRLF
            yield CRLF
            yield dumps(jsonResult, item_sort_key=_item_sort_key, indent=2)
        finally:
            collectLogForScope(search=logDict)

    def jsonResponse(self, args):
        t0 = self._timeNow()
        result = yield self.any.executeQuery(**args.queryKwargs)

        queryTime = self._timeNow() - t0
        total, hits = result.total, result.hits
        jsonResponse = JsonDict({'total': total})

        if hits:
            if hasattr(result, 'items'):
                jsonResponse['items'] = result.items
            else:
                jsonResponse['items'] = yield self._getItems(identifiers=[hit.id for hit in hits], recordSchema=args.recordSchema)

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

        return jsonResponse

    def _defaultGetItems(self, identifiers, recordSchema):
        result = []
        for identifier in identifiers:
            result.append((yield self.any.retrieveData(identifier=identifier, name=recordSchema)))
        return result

    def _observerGetItems(self, identifiers, recordSchema):
        return [self.call.getItem(identifier=identifier, recordSchema=recordSchema) for identifier in identifiers]
        yield

    def _timeNow(self):
        return time()

    def _querytime(self, t):
        return Decimal(t).quantize(MILLIS)

class _Arguments(object):
    def __init__(self, arguments, default_facet_terms_count, maximum_record_number, page_size, default_record_schema):
        query = arguments.pop('query', [None])[0]
        if query is None:
            raise MissingArgument('query')
        self._request = dict(query=query)
        self._next_request = dict(query=query)
        self.query_expression = WebQuery(query, antiUnaryClause="*").query
        page = getInt(arguments, 'page', 1)
        if page <= 0:
            raise InvalidArgument('page', 'expected value > 0')
        if 'page' in arguments:
            self._request['page'] = page
            self._next_request['page'] = page
            arguments.pop('page')
        self.recordSchema = arguments.pop('recordSchema', [default_record_schema])[0]
        pageSize = getInt(arguments, 'page-size', page_size)
        if pageSize < 0:
            raise InvalidArgument('page-size', 'expected value >= 0')
        if 'page-size' in arguments:
            self._request['page-size'] = pageSize
            self._next_request['page-size'] = pageSize
            arguments.pop('page-size')
        self.start = (page - 1) * pageSize
        if self.start > maximum_record_number:
            raise InvalidArgument('page', 'expected value <= {}'.format((maximum_record_number + pageSize -1)//pageSize))
        self.stop = min(self.start + pageSize, maximum_record_number)
        facets = arguments.pop('facet', [])
        queryFacets = []
        for facet in facets:
            fieldname = facet
            maxTerms = default_facet_terms_count
            splitted = facet.rsplit(':', 1)
            try:
                maxTerms = int(splitted[1]) if len(splitted) > 1 else default_facet_terms_count
                fieldname = splitted[0]
            except ValueError:
                pass
            queryFacets.append(dict(fieldname=fieldname, maxTerms=maxTerms, sortBy=DRILLDOWN_SORTBY_COUNT))
            self._request.setdefault('facet',[]).append({'index': fieldname, 'max-terms': maxTerms})
            facet_term_count = ':{0}'.format(maxTerms) if maxTerms != default_facet_terms_count else ''
            self._next_request.setdefault('facet',[]).append(fieldname + facet_term_count)
        facetFilters = arguments.pop('facet-filter', [])
        if facetFilters:
            self._request['facet-filter'] = []
            self._next_request['facet-filter'] = []
            q = QueryExpression.nested('AND')
            q.operands.append(self.query_expression)
            for facetFilter in facetFilters:
                if '=' not in facetFilter:
                    raise InvalidArgument('facet-filter', "expected <field>=<value> as a filter")
                index, term = facetFilter.split('=', 1)
                q.operands.append(QueryExpression.searchterm(index=index, relation='exact', term=term))
                self._request['facet-filter'].append({'index':index, 'term':term})
                self._next_request['facet-filter'].append('{}={}'.format(index, term))
            self.query_expression = q
        self.queryKwargs=dict(
                start=self.start,
                stop=self.stop,
                query=self.query_expression,
                facets=queryFacets or None,
            )
        extra_arguments = {}
        for k, v in arguments.items():
            if k.startswith('x-'):
                extra_arguments[k] = v
            else:
                raise BadArgument(k)
        if extra_arguments:
            self._request.update(extra_arguments)
            self._next_request.update(extra_arguments)
            self.queryKwargs['extraArguments'] = extra_arguments

    @property
    def request(self):
        return dict(self._request)


    def pageDict(self, pageAddition, path):
        page = self._next_request.get('page', 1) + pageAddition
        return dict(
                page=page,
                link='{0}?{1}'.format(
                    path,
                    urlencode(sorted(dict(self._next_request, page=page).items()))
                ),
            )

    def facetDict(self, path, fieldname, term, displayValue):
        termDict = dict(self._next_request)
        facetFilter = set(termDict.get('facet-filter', []))
        facetFilter.add("{0}={1}".format(fieldname, term['term']))
        termDict['facet-filter'] = list(facetFilter)
        result = dict(
            count=term['count'],
            value=term['term'],
            link="{0}?{1}".format(path, urlencode(sorted(termDict.items())))
        )
        if displayValue is not None:
            result['displayValue'] = displayValue
        return result

urlencode = lambda arg: _urlencode(arg, doseq=True)

MILLIS = Decimal('0.001')

class MissingArgument(ValueError):
    def __init__(self, argument):
        ValueError.__init__(self, "Missing required argument: {}".format(repr(argument)))

class InvalidArgument(ValueError):
    def __init__(self, argument, message):
        ValueError.__init__(self, "Invalid argument: {}, {}".format(repr(argument), message))

class BadArgument(ValueError):
    def __init__(self, argument):
        ValueError.__init__(self, "Bad argument: {} is an illegal parameter".format(repr(argument)))

def getInt(arguments, key, default):
    try:
        return int(arguments.get(key, [default])[0])
    except ValueError:
        raise InvalidArgument(key, 'expected integer')

_first={key:nr for nr, key in enumerate(reversed(['total', 'items', 'response', 'request']), start=1)}
_last={key:nr for nr, key in enumerate(['next', 'previous', 'version'], start=1)}
def _item_sort_key(xxx_todo_changeme):
    (k,v) = xxx_todo_changeme
    return ' ' * _first.get(k,0) + chr(127) * _last.get(k,0) + k

