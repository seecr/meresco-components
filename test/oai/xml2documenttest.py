# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##


from cq2utils.cq2testcase import CQ2TestCase
from cq2utils.calltrace import CallTrace

from merescocomponents.oai.xml2document import Xml2Document, TEDDY_NS
from merescocomponents.facetindex import Document, IDFIELD
from amara import binderytools

class Xml2DocumentTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.converter = Xml2Document()

    def testId(self):
        document = self.converter._create('id', binderytools.bind_string('<fields/>').fields)
        self.assertTrue(isinstance(document, Document))
        luceneDoc = document._document
        self.assertEquals('id', luceneDoc.get(IDFIELD))

    def testIndexField(self):
        document = self.converter._create('id', binderytools.bind_string('<fields><tag>value</tag></fields>').fields)
        luceneDoc = document._document
        field = luceneDoc.getFields('fields.tag')[0]
        self.assertEquals('value', field.stringValue())
        self.assertEquals('fields.tag', field.name())
        self.assertEquals(True, field.isTokenized())

    def testIndexTokenizedField(self):
        document = self.converter._create('id', binderytools.bind_string('<fields xmlns:teddy="%s">\n<tag teddy:tokenize="false">value</tag></fields>' % TEDDY_NS).fields)
        luceneDoc = document._document
        field = luceneDoc.getFields('fields.tag')[0]
        self.assertEquals('value', field.stringValue())
        self.assertEquals('fields.tag', field.name())
        self.assertEquals(False, field.isTokenized())

    def testMultiLevel(self):
        document = self.converter._create('id', binderytools.bind_string("""<document xmlns:t="%s">
        <tag t:tokenize="false">value</tag>
        <lom>
            <general>
                <title>The title</title>
            </general>
        </lom>
    </document>""" % TEDDY_NS).document)
        luceneDoc = document._document
        field = luceneDoc.getFields('document.tag')[0]
        self.assertEquals('value', field.stringValue())
        self.assertEquals('document.tag', field.name())
        self.assertEquals(False, field.isTokenized())
        field = luceneDoc.getFields('document.lom.general.title')[0]
        self.assertEquals('The title', field.stringValue())
        self.assertEquals('document.lom.general.title', field.name())
        self.assertEquals(True, field.isTokenized())

    def testSkip(self):
        document = self.converter._create('id', binderytools.bind_string("""<document xmlns:t="%s">
        <xmlfields t:skip="true">
            <title>The title</title>
            <general><identifier>ID</identifier></general>
        </xmlfields>
    </document>""" % TEDDY_NS).document)
        luceneDoc = document._document
        fields = luceneDoc.getFields('title')
        self.assertTrue(fields != None)
        field = fields[0]
        self.assertEquals('The title', field.stringValue())
        self.assertEquals('title', field.name())
        self.assertEquals(True, field.isTokenized())
        field = luceneDoc.getFields('general.identifier')[0]
        self.assertEquals('ID', field.stringValue())
        self.assertEquals('general.identifier', field.name())
        self.assertEquals(True, field.isTokenized())

    def testSkipRootTag(self):
        document = self.converter._create('id', binderytools.bind_string("""<document xmlns:t="%s" t:skip="true">
        <dc>
            <title>The title</title>
        </dc>
    </document>""" % TEDDY_NS).document)
        luceneDoc = document._document
        fields = luceneDoc.getFields('dc.title')
        self.assertTrue(fields != None)

    def testIsObservable(self):
        observer = CallTrace("Observer")
        self.converter.addObserver(observer)
        list(self.converter.add("id_0", "partName", binderytools.bind_string('<fields/>').fields))

        self.assertEquals(1, len(observer.calledMethods))
        self.assertEquals("addDocument", observer.calledMethods[0].name)
        self.assertEquals(Document, observer.calledMethods[0].args[0].__class__)
