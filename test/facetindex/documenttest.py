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

import unittest
from cq2utils import CallTrace
from merescocomponents.facetindex.document import IDFIELD, Document, DocumentException

class DocumentTest(unittest.TestCase):

    def testEmptyDocumentFails(self):
        d = Document('1')
        self.assertEquals(d.fields(), [IDFIELD])
        try:
            d.validate()
            self.fail()
        except DocumentException,e:
            self.assertEquals("Empty document", str(e))

    def testEmptyIdFails(self):
        try:
            d = Document(' ')
            self.fail()
        except DocumentException,e:
            self.assertEquals("Invalid ID: ' '", str(e))

    def testIdMustBeString(self):
        try:
            d = Document(1234)
            self.fail()
        except DocumentException,e:
            self.assertEquals("Invalid ID: '1234'", str(e))

    def testIdCanBeUnicode(self):
        d = Document(u'havefun')

    def testAddInvalidField(self):
        d = Document('1234')
        try:
            d.addIndexedField(None, None)
            self.fail()
        except DocumentException,e:
            self.assertEquals('Invalid fieldname: "None"', str(e))
        self.assertEquals(d.fields(), [IDFIELD])

    def testIgnoreEmptyField(self):
        d = Document('1234')
        d.addIndexedField("x", None)
        self.assertEquals(d.fields(), [IDFIELD])

    def testAddField(self):
        d = Document('1234')
        d.addIndexedField('x', 'a')
        d.addIndexedField('y', 'b')
        self.assertEquals(d.fields(), [IDFIELD, 'x', 'y'])
        d.validate()

    def testReservedFieldName(self):
        d = Document('1234')
        try:
            d.addIndexedField(IDFIELD, 'not allowed')
            self.fail()
        except DocumentException,e:
            self.assertEquals('Invalid fieldname: "%s"' % IDFIELD, str(e))

    def testAddSameFieldTwice(self):
        d = Document('1234')
        d.addIndexedField('x', 'a')
        d.addIndexedField('x', 'b')
        d.addToIndexWith(CallTrace("IndexWriter"))
        self.assertEquals([IDFIELD, 'x', 'x'], d.fields())

    def testAsDict(self):
        d = Document('1234')
        d.addIndexedField('field', 'value1')
        d.addIndexedField('field', 'value2')
        self.assertEquals({'__id__': ['1234'], 'field': ['value1', 'value2']}, d.asDict())

    def testSetBoost(self):
        d = Document('987')
        d.setBoost(0.1234)
        indexwriter = CallTrace('indexwriter')
        d.addToIndexWith(indexwriter)
        self.assertAlmostEquals(0.1234, indexwriter.calledMethods[0].args[0].getBoost())

    def testAddStoredField(self):
        d = Document('987')
        d.addIndexedField('field0', 'term', store=True)
        d.addIndexedField('field1', 'term')
        indexwriter = CallTrace('indexwriter')
        d.addToIndexWith(indexwriter)
        luceneDoc = indexwriter.calledMethods[0].args[0]
        self.assertTrue(luceneDoc.getField('field0').isStored())
        self.assertFalse(luceneDoc.getField('field1').isStored())

    def testLongStringValueInDocumentAsDict(self):
        d = Document('identifier')
        value = 'a' * 4096 * 2
        d.addIndexedField('key', value)
        self.assertEquals([value], d.asDict()['key'])  # previously caused buffer overrun... (manifested itself by hanging/termination)

