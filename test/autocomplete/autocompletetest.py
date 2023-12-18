# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2009-2011 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2009-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2016, 2020-2021, 2023 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2011, 2014, 2020-2021, 2023 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015-2016 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from meresco.components.autocomplete import Autocomplete, PrefixBasedSuggest

from testhelpers import Response as SolrResponse
from seecr.test import SeecrTestCase, CallTrace
from weightless.core import be
from weightless.core.utils import generatorToString
from seecr.test.io import stderr_replaced

class AutocompleteTest(SeecrTestCase):

    def setUp(self):
        super(AutocompleteTest, self).setUp()
        self.observer = CallTrace('observer')
        self._setUpAuto()

    def _setUpAuto(self, prefixBasedSearchKwargs=None):
        prefixBasedSearchKwargs = {} if prefixBasedSearchKwargs is None else prefixBasedSearchKwargs
        queryTemplate = '/sru?version=1.1&operation=searchRetrieve&query={searchTerms}'
        htmlQueryTemplate = '/demo?q={searchTerms}'
        self.auto = be((Autocomplete(
                baseUrl='https://auto.example.org',
                path='/some/path',
                templateQuery=queryTemplate,
                htmlTemplateQuery=htmlQueryTemplate,
                shortname="Web Search",
                description="Use this web search to search something"),
            (PrefixBasedSuggest(
                    defaultLimit=50,
                    defaultField='lom',
                    **prefixBasedSearchKwargs
                ),
                (self.observer,),
            ),
        ))

    def testDefaultHandleRequest(self):
        response = SolrResponse()
        response.hits = ['term0', 'term&/"']
        response.total = 2
        response.qtime = 5
        def prefixSearch(**kwargs):
            return response
            yield
        self.observer.methods['prefixSearch'] = prefixSearch

        header, body = generatorToString(self.auto.handleRequest(path='/path', arguments={'prefix':['Te']})).split('\r\n'*2)

        self.assertTrue("Content-Type: application/x-suggestions+json" in header, header)
        self.assertEqual("""["Te", ["term0", "term&/\\""]]""", body)
        self.assertEqual(['prefixSearch'], [m.name for m in self.observer.calledMethods])
        self.assertEqual({'prefix':'te', 'fieldname':'lom', 'limit':50}, self.observer.calledMethods[0].kwargs)

    def testHandleRequest(self):
        response = SolrResponse()
        response.hits = ['term0', 'term&/"']
        response.total = 2
        response.qtime = 5
        def prefixSearch(**kwargs):
            return response
            yield
        self.observer.methods['prefixSearch'] = prefixSearch

        header, body = generatorToString(self.auto.handleRequest(path='/path', arguments={'prefix':['te'], 'limit': ['5'], 'field': ['field.one']})).split('\r\n'*2)

        self.assertTrue("Content-Type: application/x-suggestions+json" in header, header)
        self.assertEqual("""["te", ["term0", "term&/\\""]]""", body)
        self.assertEqual(['prefixSearch'], [m.name for m in self.observer.calledMethods])
        self.assertEqual({'prefix':'te', 'fieldname':'field.one', 'limit':5}, self.observer.calledMethods[0].kwargs)

    @stderr_replaced
    def testOldStyleAutocomplete(self):
        queryTemplate = '/sru?version=1.1&operation=searchRetrieve&query={searchTerms}'
        self.auto = be((Autocomplete(
                host='localhost',
                port=8000,
                path='/some/path',
                templateQuery=queryTemplate,
                shortname="Web Search",
                description="Use this web search to search something",
                defaultLimit=50,
                defaultField='lom',
            ),
            (self.observer,),
        ))
        response = SolrResponse()
        response.hits = ['term0', 'term&/"']
        response.total = 2
        response.qtime = 5
        def prefixSearch(**kwargs):
            return response
            yield
        self.observer.methods['prefixSearch'] = prefixSearch

        header, body = generatorToString(self.auto.handleRequest(path='/path', arguments={'prefix':['te'], 'limit': ['5'], 'field': ['field.one']})).split('\r\n'*2)

        self.assertTrue("Content-Type: application/x-suggestions+json" in header, header)
        self.assertEqual("""["te", ["term0", "term&/\\""]]""", body)
        self.assertEqual(['prefixSearch'], [m.name for m in self.observer.calledMethods])
        self.assertEqual({'prefix':'te', 'fieldname':'field.one', 'limit':5}, self.observer.calledMethods[0].kwargs)

        result = generatorToString(self.auto.handleRequest(
            path='/path/opensearchdescription.xml',
            arguments={}))
        header,body = result.split('\r\n'*2)

        self.assertTrue("Content-Type: text/xml" in header, header)
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
    <ShortName>Web Search</ShortName>
    <Description>Use this web search to search something</Description>
    <Url type="text/xml" method="get" template="http://localhost:8000/sru?version=1.1&amp;operation=searchRetrieve&amp;query={searchTerms}"/>
    <Url type="application/x-suggestions+json" template="http://localhost:8000/some/path?prefix={searchTerms}"/>
</OpenSearchDescription>""", body)

    def testMinimumLength(self):
        self._setUpAuto(prefixBasedSearchKwargs=dict(minimumLength=5))
        header, body = generatorToString(self.auto.handleRequest(path='/path', arguments={'prefix':['test']})).split('\r\n'*2)

        self.assertTrue("Content-Type: application/x-suggestions+json" in header, header)
        self.assertEqual("""["test", []]""", body)
        self.assertEqual([], [m.name for m in self.observer.calledMethods])

    def testDefaultMinimumLength(self):
        header, body = generatorToString(self.auto.handleRequest(path='/path', arguments={'prefix':['t']})).split('\r\n'*2)

        self.assertTrue("Content-Type: application/x-suggestions+json" in header, header)
        self.assertEqual("""["t", []]""", body)
        self.assertEqual([], [m.name for m in self.observer.calledMethods])

    def testOpenSearchDescriptionXml(self):
        result = generatorToString(self.auto.handleRequest(
            path='/path/opensearchdescription.xml',
            arguments={}))
        header,body = result.split('\r\n'*2)

        self.assertTrue("Content-Type: text/xml" in header, header)
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
    <ShortName>Web Search</ShortName>
    <Description>Use this web search to search something</Description>
    <Url type="text/xml" method="get" template="https://auto.example.org/sru?version=1.1&amp;operation=searchRetrieve&amp;query={searchTerms}"/>
    <Url type="text/html" method="get" template="https://auto.example.org/demo?q={searchTerms}"/>
    <Url type="application/x-suggestions+json" template="https://auto.example.org/some/path?prefix={searchTerms}"/>
</OpenSearchDescription>""", body)

    def testOpenSearchWithoutHtmlAndPort80(self):
        queryTemplate = '/sru?version=1.1&operation=searchRetrieve&query={searchTerms}'
        self.auto = be((Autocomplete(
                host='localhost',
                port=80,
                path='/some/path',
                templateQuery=queryTemplate,
                shortname="Web Search",
                description="Use this web search to search something",
                defaultLimit=50,
                defaultField='lom',
            ),
            (self.observer,),
        ))
        result = generatorToString(self.auto.handleRequest(
            path='/path/opensearchdescription.xml',
            arguments={}))
        header,body = result.split('\r\n'*2)

        self.assertTrue("Content-Type: text/xml" in header, header)
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
    <ShortName>Web Search</ShortName>
    <Description>Use this web search to search something</Description>
    <Url type="text/xml" method="get" template="http://localhost/sru?version=1.1&amp;operation=searchRetrieve&amp;query={searchTerms}"/>
    <Url type="application/x-suggestions+json" template="http://localhost/some/path?prefix={searchTerms}"/>
</OpenSearchDescription>""", body)

    def testJQueryJS(self):
        result = generatorToString(self.auto.handleRequest(
            path='/path/jquery.js',
            arguments={}))
        header,body = result.split('\r\n'*2)
        self.assertTrue('jQuery JavaScript Library' in body, body[:300])
        try:
            self.assertTrue('Content-Type: application/x-javascript' in header, header)
        except AssertionError:
            self.assertTrue('Content-Type: application/javascript' in header, header)

    def testJQueryAutocompleteJS(self):
        result = generatorToString(self.auto.handleRequest(
            path='/path/jquery.autocomplete.js',
            arguments={}))
        header,body = result.split('\r\n'*2)
        self.assertTrue('Extending jQuery with autocomplete' in body, body[:300])
        try:
            self.assertTrue('Content-Type: application/x-javascript' in header, header)
        except AssertionError:
            self.assertTrue('Content-Type: application/javascript' in header, header)

    def testAutocompleteCSS(self):
        result = generatorToString(self.auto.handleRequest(
            path='/path/autocomplete.css',
            arguments={}))
        header,body = result.split('\r\n'*2)
        self.assertTrue('jqac-' in body, body[:300])
        self.assertTrue('Content-Type: text/css' in header, header)
