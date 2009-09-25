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
from unittest import TestCase

from PyLucene import TermQuery, Term, BooleanQuery, BooleanClause, PhraseQuery, PrefixQuery

from cqlparser import parseString as parseCql, UnsupportedCQL
from merescocomponents.facetindex.cqlparsetreetolucenequery import LuceneQueryComposer

class CqlParseTreeToLuceneQueryTest(TestCase):

    def testOneTermOutput(self):
        self.assertConversion(TermQuery(Term("unqualified", "cat")), "cat")

    def testRightHandSideIsLowercase(self):
        self.assertConversion(TermQuery(Term("unqualified", "cat")), "CaT")

    def testOneTermOutputWithANumber(self):
        self.assertConversion(TermQuery(Term("unqualified", "2005")), "2005")

    def testPhraseOutput(self):
        query = PhraseQuery()
        query.add(Term("unqualified", "cats"))
        query.add(Term("unqualified", "dogs"))
        self.assertConversion(query,'"cats dogs"')

    def testPhraseQueryIsStandardAnalyzed(self):
        expected = PhraseQuery()
        for term in ["vol.118", "2008", "nr.3", "march", "p.435-444"]:
            expected.add(Term("unqualified", term))
        input = '"vol.118 (2008) nr.3 (March) p.435-444"'
        self.assertConversion(expected, input)

    def testOneTermPhraseQueryUsesStandardAnalyzed(self):
        expected = PhraseQuery()
        expected.add(Term('unqualified', 'aap'))
        expected.add(Term('unqualified', 'noot'))
        self.assertConversion(expected, 'aap:noot')

    def testStandardAnalyserWithoutStopWords(self):
        expected = PhraseQuery()
        for term in ["no", "is", "the", "only", "option"]:
            expected.add(Term("unqualified", term))
        self.assertConversion(expected, '"no is the only option"')


    def testIndexRelationTermOutput(self):
        self.assertConversion(TermQuery(Term("animal", "cats")), 'animal=cats')
        query = PhraseQuery()
        query.add(Term("animal", "cats"))
        query.add(Term("animal", "dogs"))
        self.assertConversion(query, 'animal="cats dogs"')
        self.assertConversion(query, 'animal="catS Dogs"')

    def testIndexRelationExactTermOutput(self):
        self.assertConversion(TermQuery(Term("animal", "hairy cats")), 'animal exact "hairy cats"')
        self.assertConversion(TermQuery(Term("animal", "Capital Cats")), 'animal exact "Capital Cats"')

    def testBooleanAndTermOutput(self):
        query = BooleanQuery()
        query.add(TermQuery(Term('unqualified', 'cats')), BooleanClause.Occur.MUST)
        query.add(TermQuery(Term('unqualified', 'dogs')), BooleanClause.Occur.MUST)
        self.assertConversion(query, 'cats AND dogs')

    def testBooleanOrTermOutput(self):
        query = BooleanQuery()
        query.add(TermQuery(Term('unqualified', 'cats')), BooleanClause.Occur.SHOULD)
        query.add(TermQuery(Term('unqualified', 'dogs')), BooleanClause.Occur.SHOULD)
        self.assertConversion(query, 'cats OR dogs')

    def testBooleanNotTermOutput(self):
        query = BooleanQuery()
        query.add(TermQuery(Term('unqualified', 'cats')), BooleanClause.Occur.MUST)
        query.add(TermQuery(Term('unqualified', 'dogs')), BooleanClause.Occur.MUST_NOT)
        self.assertConversion(query, 'cats NOT dogs')

    def testBraces(self):
        self.assertConversion(TermQuery(Term('unqualified', 'cats')), '(cats)')
        innerQuery = BooleanQuery()
        innerQuery.add(TermQuery(Term('unqualified', 'cats')), BooleanClause.Occur.MUST)
        innerQuery.add(TermQuery(Term('unqualified', 'dogs')), BooleanClause.Occur.MUST)
        outerQuery = BooleanQuery()
        outerQuery.add(innerQuery, BooleanClause.Occur.SHOULD)
        outerQuery.add(TermQuery(Term('unqualified', 'mice')), BooleanClause.Occur.SHOULD)

        self.assertConversion(outerQuery, '(cats AND dogs) OR mice')

    def testBoost(self):
        query = TermQuery(Term("title", "cats"))
        query.setBoost(2.0)
        self.assertConversion(query, "title =/boost=2.0 cats")

    def testUnqualifiedTermFields(self):
        composer = LuceneQueryComposer(unqualifiedTermFields=[("field0", 0.2), ("field1", 2.0)])
        ast = parseCql("value")
        result = composer.compose(ast)
        query = BooleanQuery()
        left = TermQuery(Term("field0", "value"))
        left.setBoost(0.2)
        query.add(left, BooleanClause.Occur.SHOULD)

        right = TermQuery(Term("field1", "value"))
        right.setBoost(2.0)
        query.add(right, BooleanClause.Occur.SHOULD)

        self.assertEquals(query, result)

    def testWildcards(self):
        query = PrefixQuery(Term('unqualified', 'prefix'))
        self.assertConversion(query, 'prefix*')
        self.assertConversion(query, 'PREfix*')
        query = PrefixQuery(Term('field', 'prefix'))
        self.assertConversion(query, 'field="PREfix*"')
        self.assertConversion(query, 'field=prefix*')
        query = TermQuery(Term('field', 'p'))
        self.assertConversion(query, 'field="P*"')
        #only prefix queries for now
        query = TermQuery(Term('field', 'post'))
        self.assertConversion(query, 'field="*post"')

        query = TermQuery(Term('field', 'prefix'))
        self.assertConversion(query, 'field=prefix**')

        result = LuceneQueryComposer(unqualifiedTermFields=[("field0", 0.2), ("field1", 2.0)]).compose(parseCql("prefix*"))

        query = BooleanQuery()
        left = PrefixQuery(Term("field0", "prefix"))
        left.setBoost(0.2)
        query.add(left, BooleanClause.Occur.SHOULD)

        right = PrefixQuery(Term("field1", "prefix"))
        right.setBoost(2.0)
        query.add(right, BooleanClause.Occur.SHOULD)

        self.assertEquals(query, result)

    def assertConversion(self, expected, input):
        result = LuceneQueryComposer(unqualifiedTermFields=[("unqualified", 1.0)]).compose(parseCql(input))
        self.assertEquals(expected, result, "expected %s['%s'], but got %s['%s']" % (repr(expected), str(expected), repr(result), str(result)))


    def testUnsupportedCQL(self):
        for relation in ['>','<', '>=', '<=']:
            try:
                LuceneQueryComposer(unqualifiedTermFields=[("unqualified", 1.0)]).compose(parseCql('index %(relation)s term' % locals()))
                self.fail()
            except UnsupportedCQL:
                pass
