## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2009-2011 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2009-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011, 2014 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015-2016 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from xml.sax.saxutils import escape as escapeXml
from meresco.core import Observable
from meresco.components.http.utils import okXml
from meresco.components.http import FileServer
from os.path import join, dirname, abspath
from warnings import warn

filesDir = join(dirname(abspath(__file__)), 'files')


class Autocomplete(Observable):
    def __init__(self, host, port, path, templateQuery, shortname, description, htmlTemplateQuery=None, name=None, **kwargs):
        Observable.__init__(self, name=name)
        self._host = host
        self._port = port
        self._path = path
        self._xmlTemplateQuery = templateQuery
        self._htmlTemplateQuery = htmlTemplateQuery
        self._shortname = shortname
        self._description = description
        self._fileServer = FileServer(documentRoot=filesDir)
        if 'defaultField' in kwargs:
            warn("Using old-style Autocomplete, please use PrefixBasedSuggest as observer.", DeprecationWarning)
            from .prefixbasedsuggest import PrefixBasedSuggest
            suggest = PrefixBasedSuggest(**kwargs)
            def _suggest(arguments):
                yield suggest._suggest(arguments=arguments, outside=self.any)
            self._suggest = _suggest
            self._templateQueryForSuggest = suggest.templateQueryForSuggest


    def handleRequest(self, arguments, path, **kwargs):
        filename = path.rsplit('/', 1)[-1]
        if filename in ['jquery.js', 'jquery.autocomplete.js', 'autocomplete.css']:
            yield self._files(filename, **kwargs)
        elif filename == 'opensearchdescription.xml':
            yield self._openSearchDescription(path=path, arguments=arguments, **kwargs)
        else:
            yield self._suggest(arguments=arguments)

    def _suggest(self, arguments):
        yield self.all.suggest(arguments=arguments)

    def _templateQueryForSuggest(self):
        return self.call.templateQueryForSuggest()

    def _openSearchDescription(self, **kwargs):
        yield okXml
        yield """<?xml version="1.0" encoding="UTF-8"?>"""
        yield """<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
    <ShortName>%(shortname)s</ShortName>
    <Description>%(description)s</Description>
    <Url type="text/xml" method="get" template="http://%(host)s:%(port)s%(xmlTemplateQuery)s"/>
    %(htmlUrl)s
    <Url type="%(contentTypeSuggest)s" template="http://%(host)s:%(port)s%(path)s?%(templateQueryForSuggest)s"/>
</OpenSearchDescription>""" % {
            'contentTypeSuggest': CONTENT_TYPE_JSON_SUGGESTIONS,
            'shortname': self._shortname,
            'description': self._description,
            'host': self._host,
            'port': self._port,
            'path': self._path,
            'xmlTemplateQuery': escapeXml(self._xmlTemplateQuery),
            'htmlUrl': '<Url type="text/html" method="get" template="http://{host}:{port}{template}"/>'.format(host=self._host, port=self._port, template=escapeXml(self._htmlTemplateQuery)) if self._htmlTemplateQuery else '',
            'templateQueryForSuggest': escapeXml(self._templateQueryForSuggest()),
        }

    def _files(self, filename, **kwargs):
        yield self._fileServer.handleRequest(path=filename, **kwargs)

CONTENT_TYPE_JSON_SUGGESTIONS = "application/x-suggestions+json"
