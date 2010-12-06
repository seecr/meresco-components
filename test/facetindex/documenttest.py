# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009-2010 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
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
from meresco.components.facetindex.document import IDFIELD, Document, DocumentException, tokenize, _pyAddToIndexWith
from meresco.components.facetindex.merescolucene import iterJ

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
        self.assertEquals([IDFIELD, 'x', 'x'], d.fields())

    def testAsDict(self):
        d = Document('1234')
        d.addIndexedField('field', 'value1')
        d.addIndexedField('field', 'value2')
        self.assertEquals({'__id__': ['1234'], 'field': ['value1', 'value2']}, d.asDict())

    def testTokenize(self):
        self.assertEquals([], tokenize(''))
        self.assertEquals(['token'], tokenize('token'))
        self.assertEquals(['token'], tokenize('TOKEN'))
        self.assertEquals(['token'], tokenize('token.'))
        self.assertEquals(['token'], tokenize("token's"))
        self.assertEquals(['token'], tokenize('t.o.k.e.n.'))
        self.assertEquals(['this', 'is', 'a', 'text'], tokenize('This is a text.'))

    def testDictWithTokenizedFields(self):
        d = Document('id')
        d.addIndexedField('tokenized', 'value1 value2', tokenize=True)
        d.addIndexedField('untokenized', 'value1 value2', tokenize=False)
        self.assertEquals({
            '__id__': ['id'],
            'tokenized': ['value1', 'value2'],
            'untokenized': ['value1 value2']
            }, d.asDict())

    def testDictWithSometimesTokenizedFields(self):
        d = Document('id')
        d.addIndexedField('fieldname', 'value1 value2', tokenize=True)
        d.addIndexedField('fieldname', 'value1 value2', tokenize=False)
        self.assertEquals({
            '__id__': ['id'],
            'fieldname': ['value1', 'value2', 'value1 value2']
            }, d.asDict())


    def testDictHasLazyTokenization(self):
        tokenizer = CallTrace('tokenizer', methods={'tokenize': lambda x:x.split()})
        d = Document('id')
        d._tokenize = tokenizer.tokenize
        d.addIndexedField('field1', 'value1 value2', tokenize=True)
        d.addIndexedField('field2', 'value3 value4', tokenize=True)
        docDict = d.asDict()
        self.assertEquals(['value1', 'value2'], docDict['field1'])
        self.assertEquals(1, len(tokenizer.calledMethods))

    def testDictKeys(self):
        d = Document('id')
        d.addIndexedField('field1', 'value1 value2', tokenize=True)
        d.addIndexedField('field1', 'value3 value4', tokenize=True)
        d.addIndexedField('field2', 'value5 value6', tokenize=True)
        self.assertEquals(set([IDFIELD, 'field1', 'field2']), d.asDict().keys())

    def testDictGet(self):
        d = Document('id')
        d.addIndexedField('field1', 'value1 value2', tokenize=True)
        d.addIndexedField('field2', 'value3 value4', tokenize=True)
        self.assertEquals(['value1', 'value2'], d.asDict().get('field1'))
        self.assertEquals(['nothing'], d.asDict().get('doesnotexist', ['nothing']))

    def testPyAddToIndexWith(self):
        indexWriter = CallTrace('indexWriter')
        luceneDoc = _pyAddToIndexWith(indexWriter, 'identifier1', [("key", "value", False), ("key", "anothervalue", False)])
        self.assertEquals([u"value", u"anothervalue"], list(iterJ(luceneDoc.getValues("key"))))

#def testDictUniqueKeysElements(self):

