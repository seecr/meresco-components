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
from merescocomponents.facetindex import DocSet
from lucenetestcase import LuceneTestCase
from merescocomponents.facetindex.docset import DocSet_combinedCardinalitySearch
from PyLucene import Term

class DocSetTest(LuceneTestCase):

    def testCreate(self):
        docset = DocSet()
        self.assertTrue(docset is not None)

    def testLength(self):
        self.assertEquals(0, len(DocSet()))
        self.assertEquals(2, len(DocSet([1,2])))

    def testInit(self):
        self.assertEquals(2, len(DocSet(xrange(2))))

    def testIterable(self):
        i = iter(DocSet())
        self.assertEquals([], list(i))

    def testIndexable(self):
        self.assertEquals(2, DocSet([1,2])[1])

    def testCombinedCardinality(self):
        self.assertEquals(1, DocSet([1,2]).combinedCardinality(DocSet([2,3])))

    def testDeleteDoc(self):
        i = DocSet(xrange(10))
        self.assertEquals([0,1,2,3,4,5,6,7,8,9], i)
        i.delete(5)
        self.assertEquals([0,1,2,3,4,  6,7,8,9], i)
        i.delete(99)
        self.assertEquals([0,1,2,3,4,  6,7,8,9], i)

    def testDeleteOfDocumentOutOfRange(self):
        # this code triggers a docset of precisely N docids, so that delete will overflow the buffer
        for i in range(100):
            ds = DocSet(range(i))
            ds.delete(9999)

    def testDeleteAndReAddMaintainsSortOrder(self):
        i = DocSet(xrange(10))
        self.assertEquals([0,1,2,3,4,5,6,7,8,9], i)
        i.delete(5)
        self.assertEquals([0,1,2,3,4,  6,7,8,9], i)
        i.add(10)
        self.assertEquals([0,1,2,3,4,  6,7,8,9,10], i)

    def assertIntersect(self, lhs, rhs):
        soll = set(lhs).intersection(set(rhs))
        intersection1 = DocSet(lhs).intersect(DocSet(rhs))
        ist1 = set(iter(intersection1))
        ist2 = set(iter(DocSet(rhs).intersect(DocSet(lhs))))
        self.assertEquals(soll, ist1)
        self.assertEquals(soll, ist2)

    def testIntersect(self):
        self.assertIntersect([], [])
        self.assertIntersect([1], [])
        self.assertIntersect([1], [1])
        self.assertIntersect([1,2], [1,2])
        self.assertIntersect([1,2], [1])
        self.assertIntersect([1,2], [2])
        self.assertIntersect([1,2], [2,3])
        self.assertIntersect([1,2], [3,4])
        self.assertIntersect([1,2], [1,3,4])
        self.assertIntersect([1,2], [1,2,3,4])
        self.assertIntersect([2,3], [1,2,3,4])
        self.assertIntersect([2,3,4], [1,2,3,4])
        self.assertIntersect([235,254,304,330,349,389,476,515,523,563,578,586,594,602,610,618,626,633,640], [304,371])

    def testReadLuceneDocs(self):
        self.createSimpleIndexWithEmptyDocuments(2)
        ds = DocSet.fromQuery(self.searcher, self.matchAllDocsQuery)
        self.assertEquals([0,1], list(iter(ds)))

    def testReadFrom_SEGMENT_TermDocs(self):
        self.createIndexWithFixedFieldAndValueDoc('field', 'value', 10)
        termEnum = self.reader.terms(Term('field',''))
        freq = termEnum.docFreq() # very fast, one attr lookup
        termDocs = self.reader.termDocs()
        termDocs.seek(termEnum)
        self.assertTrue('SegmentTermDocs' in str(termDocs))
        docs = DocSet.fromTermDocs(termDocs, freq)
        self.assertEquals(range(10), list(iter(docs)))

    def testReadFrom_MULTI_TermDocs(self):
        self.createIndexWithFixedFieldAndValueDoc('field', 'value', 11)
        termEnum = self.reader.terms(Term('field',''))
        freq = termEnum.docFreq() # very fast, one attr lookup
        termDocs = self.reader.termDocs()
        termDocs.seek(termEnum)
        self.assertTrue('MultiTermDocs' in str(termDocs))
        docs = DocSet.fromTermDocs(termDocs, freq)
        self.assertEquals(range(11), list(iter(docs)))

    def testReadFrom_MULTI_TermDocsWithMoreDocs(self):
        self.createIndexWithFixedFieldAndValueDoc('field', 'value', 19)
        termEnum = self.reader.terms(Term('field',''))
        freq = termEnum.docFreq() # very fast, one attr lookup
        termDocs = self.reader.termDocs()
        termDocs.seek(termEnum)
        self.assertTrue('MultiTermDocs' in str(termDocs))
        docs = DocSet.fromTermDocs(termDocs, freq)
        self.assertEquals(range(19), list(iter(docs)))

    def testSearchAlgorithm(self):
        def assertSearchCardinality(lhList, rhList):
            expected = len(set(lhList).intersection(rhList))
            lhDocSet = DocSet(lhList)
            rhDocSet = DocSet(rhList)
            self.assertEquals(expected, DocSet_combinedCardinalitySearch(lhDocSet, rhDocSet))
            self.assertEquals(expected, DocSet_combinedCardinalitySearch(rhDocSet, lhDocSet))
        assertSearchCardinality([0,1], [0,1,2,3])
        assertSearchCardinality([], [])
        assertSearchCardinality([0,1,2,3,4,5], [0,1,2,3,4,5])
        assertSearchCardinality([0,1,2,3,4,5], [0,1,2      ])
        assertSearchCardinality([0,1,2,3,4,5], [      3,4,5])
        assertSearchCardinality([0,1,2,3,4,5], [    2,3,4  ])
        assertSearchCardinality([3,4,5,6,7,8], [0,1,2,3,4,5])
        assertSearchCardinality([3,4,5,6,7,8], [            6,7,8,9,10])
        assertSearchCardinality([], [])
        assertSearchCardinality([1,4], [2,4])       #tricky one, failed after deployment
        assertSearchCardinality([1,4,5], [1,4,6])   #idem
        assertSearchCardinality(range(235,640), [304,371])   #idem

    def testContainsDocId(self):
        d = DocSet([0, 4])
        self.assertTrue(0 in d)
        self.assertFalse(1 in d)
        self.assertFalse(3 in d)
        self.assertTrue(4 in d)
        self.assertFalse(5 in d)

    def testSimpleMerge(self):
        a = DocSet([])
        b = DocSet([2])
        a.merge(b)
        self.assertEquals(1, len(a))
        self.assertEquals(2, a[0])

    def testMerge(self):
        a = DocSet([1, 2, 4])
        b = DocSet([2, 3])
        a.merge(b)
        self.assertEquals(4, len(a))
        self.assertEquals(DocSet([1, 2, 3, 4]), a)

    def testMerge(self):
        a = DocSet([2, 4])
        b = DocSet([1, 3])
        a.merge(b)
        self.assertEquals(4, len(a))
        self.assertEquals(DocSet([1, 2, 3, 4]), a)

    def testIntersectCausesPoolReallocWhichMustNotAbort(self):
        a = DocSet([1,3])
        b = DocSet([1,2,3])
        results = []
        for i in xrange(67890):
            results.append(a.intersect(b))
