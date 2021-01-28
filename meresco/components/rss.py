## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2013, 2015, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from xml.sax.saxutils import escape as xmlEscape

from urllib.parse import parse_qs
from urllib.parse import urlsplit

from meresco.core import Observable
from meresco.components.sru.sruparser import SruMandatoryParameterNotSuppliedException
from meresco.components.http import utils as httputils

from cqlparser import cqlToExpression
from cqlparser.cqlparser import CQLParseException
from meresco.components.web import WebQuery

class BadRequestException(Exception):
    pass

class Rss(Observable):

    def __init__(self, title, description, link, antiUnaryClause='', **sruArgs):
        Observable.__init__(self)
        self._title = title
        self._description = description
        self._link = link
        self._antiUnaryClause = antiUnaryClause
        self._sortKeys = sruArgs.get('sortKeys', None)
        self._maximumRecords = sruArgs.get('maximumRecords', 10)

    def handleRequest(self, RequestURI='', **kwargs):
        yield httputils.okRss
        yield """<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>"""
        try:
            Scheme, Netloc, Path, Query, Fragment = urlsplit(RequestURI)
            arguments = parse_qs(Query)
            sortKeys = arguments.get('sortKeys', [self._sortKeys])[0]
            sortBy, sortDescending = None, None
            if sortKeys:
                sortBy, ignored, sortDescending = sortKeys.split(',')
                sortDescending = sortDescending == '1'

            maximumRecords = int(arguments.get('maximumRecords', [self._maximumRecords])[0])
            query = arguments.get('query', [''])[0]
            filters = arguments.get('filter', [])
            startRecord = 1

            if not query and not self._antiUnaryClause:
                raise SruMandatoryParameterNotSuppliedException("query")
            webquery = WebQuery(query, antiUnaryClause=self._antiUnaryClause)
            for filter in filters:
                if not ':' in filter:
                    raise BadRequestException('Invalid filter: %s' % filter)
                field,term = filter.split(':', 1)
                webquery.addFilter(field, term)

            ast = webquery.ast
        except (SruMandatoryParameterNotSuppliedException, BadRequestException, CQLParseException) as e:
            yield '<title>ERROR %s</title>' % xmlEscape(self._title)
            yield '<link>%s</link>' % xmlEscape(self._link)
            yield "<description>An error occurred '%s'</description>" % xmlEscape(str(e))
            yield """</channel></rss>"""
            return
        yield '<title>%s</title>' % xmlEscape(self._title)
        yield '<description>%s</description>' % xmlEscape(self._description)
        yield '<link>%s</link>' % xmlEscape(self._link)

        SRU_IS_ONE_BASED = 1 #And our RSS plugin is closely based on SRU
        yield self._yieldResults(
                query=cqlToExpression(ast),
                start=startRecord - SRU_IS_ONE_BASED,
                stop=startRecord - SRU_IS_ONE_BASED+maximumRecords,
                sortBy=sortBy,
                sortDescending=sortDescending)

        yield """</channel>"""
        yield """</rss>"""

    def _yieldResults(self, query=None, start=0, stop=9, sortBy=None, sortDescending=False):
        response = yield self.any.executeQuery(
            query=query,
            start=start,
            stop=stop,
            sortKeys=[{'sortBy': sortBy, 'sortDescending': sortDescending}] if sortBy is not None else None
        )
        total, hits = response.total, response.hits
        for hit in hits:
            yield self.call.getRecord(identifier=hit.id)
