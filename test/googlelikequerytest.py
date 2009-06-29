## begin license ##
#
#    "Delft-Tilburg" (delfttilburg) is a package containing shared code
#    between the Delft "Discover" and Tilburg "Beter Zoeken & Vinden" projects.
#    Both projects are based on Meresco Software (http://meresco.com)
#    Copyright (C) 2008-2009 Technische Universiteit Delft http://www.tudelft.nl
#    Copyright (C) 2008-2009 Universiteit van Tilburg http://www.uvt.nl
#    Copyright (C) 2008-2009 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of "Delft-Tilburg".
#
#    "Delft-Tilburg" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "Delft-Tilburg" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "Delft-Tilburg"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from unittest import TestCase

from merescocore.framework import Observable
from delfttilburg.googlelikequery import _joinFieldAndTerm, createParseTree, unGoogleQuery, isGoogleLikeQuery, isValidGoogleQuery, GoogleLikeQuery, createAndQuery, _joinFieldAndTerm

class GoogleLikeQueryTest(TestCase):
    def testJoinFieldAndTerm(self):
        def assertQuery(expected, fieldAndTerms):
            self.assertEquals(expected, _joinFieldAndTerm(fieldAndTerms))

        assertQuery('', [])
        assertQuery('field exact term', ['field:term'])
        assertQuery('(field1 exact term1) AND (field2 exact term2)', ['field1:term1', 'field2:term2'])

    def testGoogleLikeParseTree(self):
        def assertCQL(expectedCQL, query, drilldownArguments, extra):
            query = unGoogleQuery(query, antiUnaryClause='meresco.exists exact true')
            parseTree, cqlQuery = createParseTree(query, drilldownArguments, extra)
            self.assertEquals(expectedCQL, cqlQuery)

        assertCQL("meresco.exists exact true NOT cats", "-cats", [], [])
        assertCQL("(meresco.exists exact true NOT cats) AND field exact term", "-cats", ['field:term'], [])
        assertCQL('(cats AND dogs) AND field exact term', "cats AND dogs", ['field:term'], [])
        assertCQL('(cats AND dogs) AND (field exact term) AND (field1 exact value1)', "cats AND dogs", ['field:term'], ['field1:value1'])
        assertCQL('(cats AND dogs) AND (field exact term) AND ((field1 exact value1) AND (field2 exact value2))', "cats AND dogs", ['field:term'], ['field1:value1', 'field2:value2'])

    def testParseTree(self):
        observable = Observable()
        observable.addObserver(GoogleLikeQuery())

        parsetree, cqlQuery = observable.any.parseQuery('', [])
        self.assertEquals('meresco.exists exact true', cqlQuery)

        parsetree, cqlQuery = observable.any.parseQuery('word1 word2 and word3', [])
        self.assertEquals('word1 AND word2 AND "and" AND word3', cqlQuery)

        parsetree, cqlQuery = observable.any.parseQuery('(cats', [])
        self.assertEquals('"(cats"', cqlQuery)

    def testParseTreeUsesExtra(self):
        observable = Observable()
        observable.addObserver(GoogleLikeQuery())

        parsetree, cqlQuery = observable.any.parseQuery('', [], extra=['drilldown.mods.subject.topic:Nederland'])
        self.assertEquals('(meresco.exists exact true) AND drilldown.mods.subject.topic exact Nederland', cqlQuery)

        parsetree, cqlQuery = observable.any.parseQuery('fiets', [], extra=['drilldown.mods.subject.topic:Nederland'])
        self.assertEquals('(fiets) AND drilldown.mods.subject.topic exact Nederland', cqlQuery)

        parsetree, cqlQuery = observable.any.parseQuery("label=", [], extra=[])
        self.assertEquals('"label="', cqlQuery)

        parsetree, cqlQuery = observable.any.parseQuery("label=\"\"", [], extra=[])
        self.assertEquals('"label="', cqlQuery)

        parsetree, cqlQuery = observable.any.parseQuery("label=\" \"", [], extra=[])
        self.assertEquals('label=" "', cqlQuery)

        parsetree, cqlQuery = observable.any.parseQuery("label=value", [], extra=[])
        self.assertEquals("label=value", cqlQuery)

        parsetree, cqlQuery = observable.any.parseQuery('label="quoted value"', [], extra=[])
        self.assertEquals('label="quoted value"', cqlQuery)

    def testSingleParenthesisIsNotValidGoogleLike(self):
        observable = Observable()
        observable.addObserver(GoogleLikeQuery())

        self.assertTrue(observable.any.isValidGoogleQuery('cats and dogs'))
        self.assertFalse(observable.any.isValidGoogleQuery('('))


    def testGoogleLikeQueryDetection(self):
        self.assertFalse(isGoogleLikeQuery('cats dogs'))
        self.assertTrue(isGoogleLikeQuery('cats and dogs'))
        self.assertFalse(isGoogleLikeQuery('cats'))
        self.assertTrue(isGoogleLikeQuery('-cats'))
        self.assertFalse(isGoogleLikeQuery('ca-ts'))
        self.assertFalse(isGoogleLikeQuery('cats-'))
        self.assertTrue(isGoogleLikeQuery('(cats)'))
        self.assertTrue(isGoogleLikeQuery('('))

    def testUnGoogleQuery(self):
        self.assertEquals('antiunary NOT cats', unGoogleQuery('-cats', antiUnaryClause="antiunary"))
        self.assertEquals('(antiunary NOT cats and dogs) or mice', unGoogleQuery('(-cats and dogs) or mice', antiUnaryClause="antiunary"))
        self.assertEquals('dogs NOT cats', unGoogleQuery('dogs -cats'))
        self.assertEquals('antiunary NOT cats AND dogs', unGoogleQuery('-cats AND dogs', antiUnaryClause="antiunary"))

    def testIsValidGoogleQuery(self):
        self.assertFalse(isValidGoogleQuery('cats AND'))
        self.assertTrue(isValidGoogleQuery('cats AND dogs'))

    def testCreateAndQuery(self):
        self.assertEquals('', createAndQuery(''))
        self.assertEquals('word', createAndQuery('word'))
        self.assertEquals('-word', createAndQuery('-word'))

        self.assertEquals('"("', createAndQuery('('))
        self.assertEquals('"(word"', createAndQuery('(word'))

        self.assertEquals('")"', createAndQuery(')'))
        self.assertEquals('"word)"', createAndQuery('word)'))
        self.assertEquals('word AND phrase', createAndQuery('word phrase'))
        self.assertEquals('word AND "phrase1 phrase2"', createAndQuery('word "phrase1 phrase2"'))
        self.assertEquals('word1 AND word2 AND "and" AND word3', createAndQuery('word1 word2 and word3'))

        self.assertEquals("label='quoted AND value'", createAndQuery("label='quoted value'"))
        self.assertEquals('label="quoted value"', createAndQuery('label="quoted value"'))


    def testJoinFieldAndTerm(self):
        self.assertEquals("field exact value", _joinFieldAndTerm(['field:value']))
        self.assertEquals("(field1 exact value1) AND (field2 exact value2)", _joinFieldAndTerm(['field1:value1', 'field2:value2']))
        self.assertEquals('field exact "word1 word2"', _joinFieldAndTerm(['field:word1 word2']))

    def testReportedProblemWithGoogleLikeQuery(self):
        self.assertTrue(isGoogleLikeQuery('fiscal OR (market municipalities)'))
        self.assertTrue(isGoogleLikeQuery('fiscal OR (market AND municipalities)'))
        self.assertTrue(isGoogleLikeQuery('fiscal OR (market OR municipalities)'))
        self.assertTrue(isGoogleLikeQuery('fiscal OR (market NOT municipalities)'))

        self.assertFalse(isValidGoogleQuery('fiscal OR (market municipalities)'))
        self.assertTrue(isValidGoogleQuery('fiscal OR (market AND municipalities)'))
        self.assertTrue(isValidGoogleQuery('fiscal OR (market OR municipalities)'))
        self.assertTrue(isValidGoogleQuery('fiscal OR (market NOT municipalities)'))

        self.assertEquals('fiscal AND "OR" AND "(market" AND "municipalities)"', createAndQuery('fiscal OR (market municipalities)'))



