## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.core import Observable
from meresco.components.http.utils import Ok as HttpOk, ContentTypeHeader, CRLF
from .autocomplete import CONTENT_TYPE_JSON_SUGGESTIONS
from meresco.components.json import JsonList

class PrefixBasedSuggest(Observable):
    def __init__(self, defaultField, defaultLimit, minimumLength=2, **kwargs):
        super(PrefixBasedSuggest, self).__init__(**kwargs)
        self._defaultField = defaultField
        self._defaultLimit = defaultLimit
        self._minimumLength = minimumLength

    def suggest(self, arguments):
        prefix = arguments['prefix'][0]

        fieldname = arguments.get('field', [self._defaultField])[0]
        limit = int(arguments.get('limit', [self._defaultLimit])[0])

        yield HttpOk
        yield ContentTypeHeader + CONTENT_TYPE_JSON_SUGGESTIONS + CRLF
        yield "Access-Control-Allow-Origin: *" + CRLF
        yield "Access-Control-Allow-Headers: X-Requested-With" + CRLF
        yield CRLF
        hits = []
        if len(prefix) >= self._minimumLength:
            response = yield self.any.prefixSearch(fieldname=fieldname, prefix=prefix.lower(), limit=limit)
            hits = response.hits
        yield JsonList([prefix, hits]).dumps()

    def templateQueryForSuggest(self):
        return 'prefix={searchTerms}'