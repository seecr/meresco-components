## begin license ##
# 
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  initiated by Stichting Bibliotheek.nl to provide a new search service
#  for all public libraries in the Netherlands. 
# 
# Copyright (C) 2009-2011 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2009-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# 
# This file is part of "NBC+ (Zoekplatform BNL)"
# 
# "NBC+ (Zoekplatform BNL)" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "NBC+ (Zoekplatform BNL)" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "NBC+ (Zoekplatform BNL)"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from xml.sax.saxutils import escape as escapeXml
from meresco.core import Observable
from meresco.components.http.utils import Ok as HttpOk, ContentTypeHeader, CRLF, okXml
from meresco.components.http import FileServer
from simplejson import dumps as dumps_json
from urllib import quote
from os.path import join, dirname, abspath

filesDir = join(dirname(abspath(__file__)), 'files')

ContentTypeJsonSuggestions = "application/x-suggestions+json"

class Autocomplete(Observable):
    def __init__(self, host, port, path, defaultField, templateQuery, defaultLimit, shortname, description, minimumLength=2):
        Observable.__init__(self)
        self._host = host
        self._port = port
        self._path = path
        self._defaultField = defaultField
        self._templateQuery = templateQuery
        self._defaultLimit = defaultLimit
        self._shortname = shortname
        self._description = description
        self._minimumLength = minimumLength
        self._fileServer = FileServer(documentRoot=filesDir)

    def handleRequest(self, arguments, path, **kwargs):
        filename = path.rsplit('/', 1)[-1]
        if filename in ['jquery.js', 'jquery.autocomplete.js', 'autocomplete.css']:
            yield self._files(filename, **kwargs)
        elif filename == 'opensearchdescription.xml':
            yield self._openSearchDescription(path=path, arguments=arguments, **kwargs)
        else:
            yield self._prefixSearch(arguments)

    def _prefixSearch(self, arguments):
        prefix = arguments['prefix'][0]

        field = arguments.get('field', [self._defaultField])[0]
        limit = int(arguments.get('limit', [self._defaultLimit])[0])
        
        terms = []
        descriptions = []

        yield HttpOk
        yield ContentTypeHeader + ContentTypeJsonSuggestions + CRLF
        yield "Access-Control-Allow-Origin: *" + CRLF
        yield "Access-Control-Allow-Headers: X-Requested-With" + CRLF
        yield CRLF
        hits = []
        if len(prefix) >= self._minimumLength:
            response = yield self.any.prefixSearch(field=field, prefix=prefix.lower(), limit=limit)
            hits = response.hits
        yield dumps_json([prefix, hits])

    def _openSearchDescription(self, **kwargs):
        yield okXml
        yield """<?xml version="1.0" encoding="UTF-8"?>"""
        yield """<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
    <ShortName>%(shortname)s</ShortName>
    <Description>%(description)s</Description>
    <Url type="text/html" method="get" template="http://%(host)s:%(port)s%(temlateQuery)s"/>
    <Url type="application/x-suggestions+json" template="http://%(host)s:%(port)s%(path)s?prefix={searchTerms}"/>
</OpenSearchDescription>""" % {
            'shortname': self._shortname,
            'description': self._description,
            'host': self._host,
            'port': self._port,
            'path': self._path,
            'temlateQuery': escapeXml(self._templateQuery),
        }

    def _files(self, filename, **kwargs):
        yield self._fileServer.handleRequest(path=filename, **kwargs)

