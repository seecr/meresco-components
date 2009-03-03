#!/usr/local/bin/python
# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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
from time import time
from merescocomponents.facetindex import DocSetList, DocSet
from merescocomponents.facetindex.docsetlist import JACCARD_ONLY
from lucenetestcase import LuceneTestCase
from PyLucene import Term, IndexReader
from cq2utils import MATCHALL

#Facts about Lucene:
# 1.  IndexReader.open() returns a MultiIndexReader reading multiple segments
# 2.  IndexReader.termDocs(Term) just does t=termDocs(); t.seek(Term)
# 3.  IndexReader.getFieldNames() is NOT sorted, it returns a HashSet.
# 4.  IndexReader.seek(TermEnum termEnum) just does seek(termEnum.term())
# 5a. TermDocs.read(int[] docs, float[] freqs) writes directly into int[]
# 5b. while int[] being a Template subclass of java.lang.Object.
# 5c. TermDocs.seek() only sets a few vars that make read() restart with first segment
# 6.  termEnum() is complex, because of merging terms from segments
# 7a. IndexReader.docFreq(Term) scans for term and is optimized for sequential access!
# 7b. TermEnum.docFreq() is only one attribute lookup!
# CONCLUSION: The fastest way would be to let TermDocs.read(int[] docs) call add on docs,
#             which directly builds a guint32 array.  Just like FakeHitCollector does.
#             Anyway, termdocs are spit out as complete lists, not iterators.
#             So, DocSet either accepts a List, or a ctypes c_uint32 array, of which
#             it assumes ownership. Both are supported by DocSet.__init__.

class DocSetListTest(LuceneTestCase):

    def testCreate(self):
        docsetlist = DocSetList()
        self.assertEquals(0, len(docsetlist))

    def testCreate2(self):
        docsetlist = DocSetList()
        self.assertEquals(0, len(docsetlist))
        try:
            docsetlist[0]
            self.fail('must raise IndexError')
        except IndexError, e:
            self.assertEquals('list index out of range', str(e))

    def testAddMore(self):
        docsetlist = DocSetList()
        ds = DocSet([1,2])
        docsetlist.add(ds)
        docsetlist.add(DocSet([3,4]))
        docsetlist.add(DocSet([5,6]))
        self.assertEquals(3, len(docsetlist))
        self.assertEquals(DocSet([1,2]), docsetlist[0])
        self.assertEquals(DocSet([3,4]), docsetlist[1])
        self.assertEquals(DocSet([5,6]), docsetlist[2])
        try:
            docsetlist[3]
            self.fail('must raise IndexError')
        except IndexError, e:
            self.assertEquals('list index out of range', str(e))

    def testAddMoreThanBufferSize(self):
        docsetlist = DocSetList()
        bufferSize = 1000
        for i in xrange(bufferSize):
            docsetlist.add(DocSet([1]))
        try:
            docsetlist.add(DocSet([99,87]))
        except IndexError, e:
            self.fail('must not raise exception')
        self.assertEquals(bufferSize+1, len(docsetlist))
        self.assertEquals(DocSet([99,87]), docsetlist[bufferSize])

    def testDoNotFreeMemory1(self):
        docsetlist = DocSetList()
        d1 = DocSet([8])
        docsetlist.add(d1)
        del d1
        self.assertEquals(8, docsetlist[0][0])

    def testDoNotFreeMemory2(self):
        docsetlist = DocSetList()
        d1 = DocSet([8])
        docsetlist.add(d1)
        d1_copy = docsetlist[0]
        del d1_copy
        self.assertEquals(8, docsetlist[0][0])

    def testCheckForDuplicateAdd(self):
        docsetlist = DocSetList()
        d1 = DocSet([8])
        docsetlist.add(d1)
        try:
            docsetlist.add(d1)
        except AssertionError, e:
            self.assertEquals('object already released, perhaps duplicate add()?', str(e))

    def testCombinedCardinalityMultiple(self):
        docsetlist = DocSetList()
        d1 = DocSet([1,2,3])
        d2 = DocSet([2,3,4])
        d3 = DocSet([3,4,5])
        docsetlist.add(d1, 'term1')
        docsetlist.add(d2, 'term2')
        docsetlist.add(d3, 'term3')
        x = DocSet([2,3,4])
        cards = docsetlist.termCardinalities(x)
        c = cards.next()
        self.assertEquals(('term1',2), c)
        self.assertEquals(('term2',3), cards.next())
        self.assertEquals(('term3',2), cards.next())
        try:
           cards.next()
           self.fail('must raise StopIteration')
        except StopIteration:
           pass

    def testCombinedCardinalityMultipleWithZeros(self):
        docsetlist = DocSetList()
        d1 = DocSet([1,2,3])
        d2 = DocSet([7,8,9]) # intersection empty
        d3 = DocSet([3,4,5])
        docsetlist.add(d1, 't0')
        docsetlist.add(d2, 't1')
        docsetlist.add(d3, 't2')
        cards = docsetlist.termCardinalities(DocSet([3,4]))
        self.assertEquals(('t0',1), cards.next())
        self.assertEquals(('t2',2), cards.next())
        cards = docsetlist.termCardinalities(DocSet([3,4]))
        self.assertEquals([('t0',1), ('t2',2)], list(cards))

    def testReadTermsFrom_SEGMENT_reader(self):
        self.createBigIndex(10, 1) # 10 records, two values 0 and 1
        termDocs = self.reader.termDocs()
        fields = self.reader.getFieldNames(IndexReader.FieldOption.ALL)
        termEnum = self.reader.terms(Term(fields[0],''))
        dsl = DocSetList.fromTermEnum(termEnum, termDocs)
        #for docset in dsl: print docset
        self.assertEquals(2, len(dsl)) # two different values/terms
        self.assertEquals(10, len(dsl[0]) + len(dsl[1]))

    def testReadTermsFrom_MULTI_reader(self):
        self.createBigIndex(13, 2) # 13 records, three values 0, 1 and 2
        termDocs = self.reader.termDocs()
        fields = self.reader.getFieldNames(IndexReader.FieldOption.ALL)
        termEnum = self.reader.terms(Term(fields[0],''))
        dsl = DocSetList.fromTermEnum(termEnum, termDocs)
        #for docset in dsl: print docset
        self.assertEquals(3, len(dsl)) # three different values/terms
        self.assertEquals(13, len(dsl[0]) + len(dsl[1]) + len(dsl[2]))

    def testGetTerms(self):
        self.createBigIndex(9, 2) # 10 records, 6 values
        termEnum = self.reader.terms(Term('field0',''))
        termDocs = self.reader.termDocs()
        dsl = DocSetList.fromTermEnum(termEnum, termDocs)
        cs = dsl.termCardinalities(DocSet([1,2,3,4,5,6,7,8,9]))
        NA = MATCHALL
        self.assertEquals([('t€rm0', NA), ('t€rm1', NA), ('t€rm2', NA)], list(cs))

    #def testAppendToRow(self):
    def testAppendDocument(self):
        docsetlist = DocSetList()
        self.assertEquals(0, len(docsetlist))
        docsetlist.addDocument(0, ['term0', 'term1'])
        self.assertEquals([('term0', 1), ('term1', 1)],
            list(docsetlist.termCardinalities(DocSet([0, 1]))))
        docsetlist.addDocument(1, ['term0', 'term1'])
        self.assertEquals([('term0', 2), ('term1', 2)],
            list(docsetlist.termCardinalities(DocSet([0, 1]))))
        docsetlist.addDocument(2, ['term0', 'term2'])
        self.assertEquals([('term0', 3), ('term1', 2), ('term2', 1)],
            list(docsetlist.termCardinalities(DocSet([0, 1, 2]))))
        try:
            docsetlist.addDocument(2, ['term0', 'term2'])
            self.fail('must raise exception')
        except Exception, e:
            self.assertTrue("non-increasing" in str(e))

    def testEmpty(self):
        m = DocSetList()
        c = list(m.termCardinalities(DocSet([])))
        self.assertEquals([], list(c))
        c = list(m.allCardinalities())
        self.assertEquals([], list(c))

    def testEmptyDoc(self):
        m = DocSetList()
        n = m.add(DocSet([]), 'a')
        c = m.termCardinalities(DocSet([1]))
        self.assertEquals([], list(c))

    def testNoResultLeft(self):
        m = DocSetList()
        n = m.add(DocSet([1]), 'b')
        c = m.termCardinalities(DocSet([2]))
        self.assertEquals([], list(c))

    def testNoResultRight(self):
        m = DocSetList()
        n = m.add(DocSet([2]), 'x')
        c = m.termCardinalities(DocSet([1]))
        self.assertEquals([], list(c))

    def testAdd(self):
        m = DocSetList()
        m.add(DocSet([0, 2, 4, 6, 8]), 'x')
        self.assertEquals([0, 2, 4, 6, 8], m[0])
        m.add(DocSet([1, 3, 5, 7, 9]), 'x')
        self.assertEquals([1, 3, 5, 7, 9], m[1])

    def testBugCausesAbort(self):
        m = DocSetList()
        m.add(DocSet([100000000]), 'x')
        m[0].add(100000001)

    def testDocSetCardinalities(self):
        m = DocSetList()
        m.add(DocSet([1, 3, 5, 7, 9]), 'x')
        m.add(DocSet([0, 2]), 'y')
        self.assertEquals([('x', 5), ('y', 2)], list( m.allCardinalities()))

    def testtermCardinalitiesOfOne(self):
        m = DocSetList()
        m.add(DocSet([0]), 'x')
        m.add(DocSet([1]), 'y')
        self.assertEquals([('x', 1), ('y', 1)], list(m.termCardinalities(DocSet([0, 1]))))
        self.assertEquals([('x', 1)], list(m.termCardinalities(DocSet([0]))))
        self.assertEquals([('y', 1)], list(m.termCardinalities(DocSet([1]))))

    def testtermCardinalitiesOfTwo(self):
        m = DocSetList()
        n = m.add(DocSet([0, 2]), 'x')
        n= m.add(DocSet([1, 3]), 'y')
        self.assertEquals([('x', 2)], list(m.termCardinalities(DocSet([0, 2]))))
        self.assertEquals([('y', 2)], list(m.termCardinalities(DocSet([1, 3]))))
        self.assertEquals([('x', 2), ('y', 2)], list(m.termCardinalities(DocSet([0, 1, 2, 3]))))
        self.assertEquals([('x', 1)], list(m.termCardinalities(DocSet([0]))))
        self.assertEquals([('y', 1)], list(m.termCardinalities(DocSet([1]))))
        self.assertEquals([('x', 1), ('y', 1)], list(m.termCardinalities(DocSet([0, 1]))))
        self.assertEquals([('x', 1)], list(m.termCardinalities(DocSet([2]))))
        self.assertEquals([('y', 1)], list(m.termCardinalities(DocSet([3]))))
        self.assertEquals([('x', 1), ('y', 1)], list(m.termCardinalities(DocSet([2, 3]))))

    def testAllOnes(self):
        m = DocSetList()
        m.add(DocSet([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]), 'x')
        m.add(DocSet([1, 3, 5, 8, 18]), 'y')
        self.assertEquals([0,1,2,3,4,5,6,7,8,9], m[0])
        self.assertEquals([1,3,5,8,18], m[1])
        self.assertEquals([('x', 1)], list(m.termCardinalities(DocSet([0]))))
        self.assertEquals([('x', 3), ('y', 1)], list(m.termCardinalities(DocSet([0,1,2]))))
        self.assertEquals([('x', 4), ('y', 2)], list(m.termCardinalities(DocSet([0,1,2,3]))))
        self.assertEquals([('x', 5), ('y', 2)], list(m.termCardinalities(DocSet([0,1,2,3,4]))))
        self.assertEquals([('x', 6), ('y', 3)], list(m.termCardinalities(DocSet([0,1,2,3,4,5]))))
        self.assertEquals([('x', 7), ('y', 3)], list(m.termCardinalities(DocSet([0,1,2,3,4,5,6]))))
        self.assertEquals([('x', 8), ('y', 3)], list(m.termCardinalities(DocSet([0,1,2,3,4,5,6,7]))))
        self.assertEquals([('x', 9), ('y', 4)], list(m.termCardinalities(DocSet([0,1,2,3,4,5,6,7,8]))))
        self.assertEquals([('x',10), ('y', 4)], list(m.termCardinalities(DocSet([0,1,2,3,4,5,6,7,8,9]))))

    def testMaxResults(self):
        m = DocSetList()
        m.add(DocSet([0, 1]), 'x')
        m.add(DocSet([1, 2, 3]), 'y')
        m.add(DocSet([1]), 'z')
        self.assertEquals(3, len(list(m.termCardinalities(DocSet([1])))))
        self.assertEquals(1, len(list(m.termCardinalities(DocSet([1]), maxResults=1))))
        self.assertEquals(2, len(list(m.termCardinalities(DocSet([1]), maxResults=2))))

    def testColumnCleanup(self):
        m = DocSetList()
        m.add(DocSet([0]), 'x')
        self.assertEquals([0], m[0])
        m.addDocument(1, 'x')
        self.assertEquals([0, 1], m[0])
        m.deleteDoc(1)
        m.addDocument(2, 'x')
        self.assertEquals([0,2], m[0])
        m.deleteDoc(9999)

    def testSortingOnCardinality(self):
        d = DocSetList()
        d.add(DocSet([2,3]), 'x')
        d.add(DocSet([1,2,3]), 'y')
        unsortedResult = d.termCardinalities(DocSet([1,2,3]))
        self.assertFalse(d.sortedOnCardinality())
        self.assertEquals([('x', 2L), ('y', 3L)], list(unsortedResult))
        d.sortOnCardinality()
        self.assertTrue(d.sortedOnCardinality())
        sortedResult = d.termCardinalities(DocSet([1,2,3]))
        self.assertEquals([('y', 3L), ('x', 2L)], list(sortedResult))

    def testUnsortedOnAdd(self):
        d = DocSetList()
        d.add(DocSet([2,3]), 'x')
        d.sortOnCardinality()
        self.assertTrue(d.sortedOnCardinality())
        d.add(DocSet([2,3]), 'x')
        self.assertFalse(d.sortedOnCardinality())

    def testUnsortedOnAddDocument(self):
        d = DocSetList()
        d.addDocument(0, ['term0'])
        d.sortOnCardinality()
        self.assertTrue(d.sortedOnCardinality())
        d.addDocument(0, ['term1'])
        self.assertFalse(d.sortedOnCardinality())
        d.sortOnCardinality()
        self.assertTrue(d.sortedOnCardinality())
        d.addDocument(1, ['term0'])
        self.assertFalse(d.sortedOnCardinality())
        self.assertEquals([[0, 1],[0]], list(d))

    def createSomeCarefullyPreparedDocsetToTestSorting(self):
        d = DocSetList()
        d.add(DocSet([0,1]), 'a')
        d.add(DocSet([0,1,2,3,4]), 'b')
        d.add(DocSet([0]), 'c')
        d.add(DocSet([0,1,2,3]), 'd')
        d.add(DocSet([0,1,2]), 'e')
        d.add(DocSet([1,2,3,4,5,6]), 'f')
        return d

    def testSortOnTerm(self):
        d = DocSetList()
        d.addDocument(0, ['a-term'])
        d.addDocument(0, ['c-term'])
        d.addDocument(0, ['b-term'])
        d.sortOnTerm()
        self.assertEquals( [('a-term', 1), ('b-term', 1), ('c-term', 1)], list(d.allCardinalities()))

    def testSortOnTermByDefault(self):
        d = DocSetList()
        d.addDocument(0, ['a-term'])
        d.addDocument(0, ['c-term'])
        d.addDocument(0, ['b-term'])
        result = d.termCardinalities(DocSet([0]))
        self.assertEquals( [('a-term', 1), ('b-term', 1), ('c-term', 1)], list(result))

    def testTopList(self):
        d = self.createSomeCarefullyPreparedDocsetToTestSorting()
        unsortedResult = d.termCardinalities(DocSet([3,4,5]), sorted=False)
        self.assertEquals([('b',2),('d',1),('f',3)], list(unsortedResult))
        d.sortOnCardinality()
        sortedResult = d.termCardinalities(DocSet([3,4,5]), sorted=True)
        self.assertEquals([('f',3),('b',2),('d',1)], list(sortedResult))
        sortedResult = d.termCardinalities(DocSet([3,4,5]), sorted=True, maxResults=2)
        self.assertEquals([('f',3),('b',2)], list(sortedResult))

    def testAutoSort(self):
        d = self.createSomeCarefullyPreparedDocsetToTestSorting()
        sortedResult = d.termCardinalities(DocSet([3,4,5]), sorted=True, maxResults=2)
        self.assertEquals([('f',3),('b',2)], list(sortedResult))

    def testContinueWhenNoMaximumIsGiven(self):
        d = DocSetList()
        d.add(DocSet([3]), 'term0')
        d.add(DocSet([0,1]), 'term1')
        d.add(DocSet([2]), 'term2')
        sortedResult = d.termCardinalities(DocSet([0,1,2,3]), sorted=True)
        self.assertEquals([('term1',2),('term0',1),('term2',1)], list(sortedResult))

    def testSortWhenLessResultsThanMaximum(self):
        d = self.createSomeCarefullyPreparedDocsetToTestSorting()
        sortedResult = d.termCardinalities(DocSet([0,1]), sorted=True, maxResults=100)
        self.assertEquals([('b', 2L), ('d', 2L), ('e', 2L), ('a', 2L), ('f', 1L),('c', 1L)], list(sortedResult))

    def testBugWithAlternatingSearchZipperCalls(self):
        THELIST=range(193)
        dsl = DocSetList()
        dsl.add(DocSet(THELIST), 'term0')
        set1 = DocSet(data=[])
        set2 = DocSet(data=[0L])

        list(dsl.termCardinalities(set1))
        list(dsl.termCardinalities(set2))
        result = list(dsl.termCardinalities(set1))

        self.assertEquals([], result)

    def testJaccard(self):
        """
        http://en.wikipedia.org/wiki/Jaccard_index

        term0 [0,1,2,3,4] query: [2,3,4]
        union: [0,1,2,3,4] => len 5
        intersection: [2,3,4] => len 3
        3/5 = 0.6 => 60 %

        term1 [3,4,5,6,7] query: [2,3,4]
        union: [2,3,4,5,6,7] => len 6
        intersection: [3,4] => len 2
        2/6 = 0.33 => 33 %

        term2 [0,4] query: [2,3,4]
        union: [0,2,3,4] => len 4
        intersection: [4] => len 1
        1/4 = 0.25 = 25 %
        """
        dsl = DocSetList()
        dsl.add(DocSet([0,1,2,3,4]), 'term0')
        dsl.add(DocSet([3,4,5,6,7]), 'term1')
        dsl.add(DocSet([0, 4]), 'term2')
        results = dsl.jaccards(DocSet([2,3,4]), 0, 100, 8, JACCARD_ONLY)

        self.assertEquals([('term0', 60), ('term1', 33), ('term2', 25)], list(results))

    def testJaccardRange(self):
        dsl = DocSetList()
        dsl.add(DocSet(range(0,5)), 'term0')
        dsl.add(DocSet(range(0,7)), 'term1')
        dsl.add(DocSet(range(0,15)), 'term2')
        dsl.add(DocSet(range(0,20)), 'term3')
        result = dsl.jaccards(DocSet([2,3,4]), 0, 100, 20, JACCARD_ONLY)
        self.assertEquals([('term0',60),('term1',42),('term2',20),('term3',15)], list(result))

        result = dsl.jaccards(DocSet([2,3,4]), 25, 59, 20, JACCARD_ONLY)
        self.assertEquals([('term1',42)], list(result))

    def testCornerCases(self):
        dsl = DocSetList()
        dsl.add(DocSet([]), 'term0')
        dsl.add(DocSet([1]), 'term1')
        dsl.add(DocSet([2,3]), 'term2')
        dsl.add(DocSet([4,5,6,7,8,9]), 'term3')

        results = dsl.jaccards(DocSet([]), 0, 100, 9, JACCARD_ONLY)
        self.assertEquals([('term3', 0L), ('term2', 0L), ('term1', 0L)], list(results))
        results = dsl.jaccards(DocSet([1]), 1, 100, 9, JACCARD_ONLY)
        self.assertEquals([('term1',100)], list(results))
        results = dsl.jaccards(DocSet([3]), 1, 100, 9, JACCARD_ONLY)
        self.assertEquals([('term2', 50L)], list(results))
        results = dsl.jaccards(DocSet([3]), 50, 100, 9, JACCARD_ONLY)
        self.assertEquals([('term2',50)], list(results))
        results = dsl.jaccards(DocSet([6]), 16, 17, 9, JACCARD_ONLY)
        self.assertEquals([('term3', 16L)], list(results))

        results = dsl.jaccards(DocSet([1,2,3,4,5,6,7,8,9]), 0, 100, 9, JACCARD_ONLY)
        self.assertEquals([('term3', 66L), ('term2', 22L), ('term1', 11L)], list(results))
        results = dsl.jaccards(DocSet([1,2,3,4,5,6,7,8,9]), 11, 22, 9, JACCARD_ONLY)
        self.assertEquals([('term2', 22L), ('term1', 11L)], list(results))

    def testZeroLengthSets(self):
        ds1 = DocSet([1])
        dsl = DocSetList()
        dsl.add(ds1, 'x')
        self.assertEquals(1, len(dsl))
        result = dsl.jaccards(DocSet([]), 0, 100, 9, JACCARD_ONLY)
        self.assertEquals([('x', 0L)], list(result))
        ds1.delete(1)
        result = dsl.jaccards(DocSet([]), 0, 100, 9, JACCARD_ONLY)
        self.assertEquals([('x', 0)], list(result))

    def testSortingOnCardinalityDoesNotRuinTermLookup(self):
        ds0 = DocSet([1,2])
        ds1 = DocSet([1,2,3])
        dsl = DocSetList()
        dsl.add(ds0, 'term0')
        dsl.add(ds1, 'term1')
        ds0new = dsl.TEST_getDocsetForTerm('term0')
        ds1new = dsl.TEST_getDocsetForTerm('term1')
        self.assertEquals(ds0, ds0new)
        self.assertEquals(ds1, ds1new)
        dsl.sortOnCardinality()
        ds0new = dsl.TEST_getDocsetForTerm('term0')
        ds1new = dsl.TEST_getDocsetForTerm('term1')
        self.assertEquals(ds0, ds0new)
        self.assertEquals(ds1, ds1new)
