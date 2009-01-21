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
from sys import stdout
from time import time
from random import random, randint, sample

from merescocomponents.facetindex import DocSetList, DocSet, Trie
from lucenetestcase import LuceneTestCase
from PyLucene import Term, IndexReader

#pystone loop for ~ 1s:
# - 1GHz laptop: 30.000
# - Discover: 70.000
# - Juicer: 60.000
# We try to have a T of ~ 1s, as to keep the numbers in the tests meaningful (~seconds)
from test.pystone import pystones
T, p = pystones(loops=50000)
print 'T=%.1fs' % T

class PerformanceTuningTest(LuceneTestCase):

    def assertTiming(self, t0, t, t1):
        self.assertTrue(t0*T < t < t1*T, t/T)

    def testWithLotsOfData(self):
        words = 'words'
        totalLength = 0
        trie = Trie()
        t = 0
        for i, word in enumerate(word.strip() for word in open(words)):
            if word:
                if type(word) == unicode:
                    word = word.encode('utf-8')
                totalLength += len(word)

                t0 = time()
                trie.add(i, word)
                t += time() - t0

        for i, word in enumerate(word.strip() for word in open(words)):
            if word:
                if type(word) == unicode:
                    word = word.encode('utf-8')
                try:
                    self.assertEquals(i, trie.getValue(word), (i, trie.getValue(word), word))
                except:
                    #trie.printit()
                    raise
                self.assertEquals(word, trie.getTerm(i), (i, word, trie.getTerm(i)))

        print
        print 'Time for', i, 'inserts:', t, "(", totalLength, "total length) (", 1000*t/i, 'ms per insert)'
        trie.nodecount()

    def testRelativeSpeed(self):
        docset1 = DocSet.forTesting(100000)
        docset2 = DocSet.forTesting(100000)
        t1, t2 = 0.0, 0.0
        for i in range(100):
            t0 = time()
            docset1.combinedCardinality(docset2)
            t1 += time() - t0
            t0 = time()
            docset2.combinedCardinality(docset1)
            t2 += time() - t0
        self.assertTiming(0.04, t1, 0.20)
        self.assertTiming(0.04, t2, 0.20)

    def testReadLuceneDocsSpeed(self):
        self.createSimpleIndexWithEmptyDocuments(1000)
        t = 0.0
        for i in range(1000):
            t0 = time()
            ds = DocSet.fromQuery(self.searcher, self.matchAllDocsQuery)
            t += time() - t0
        self.assertTrue(0.05*T < t < 0.2*T, t)  # in ~milliseconds!
        self.assertEquals(range(1000), list(iter(ds)))

    def testVariousCornerCases(self):
        odd  = DocSet('', (x for x in xrange(20000) if     x&1))
        even = DocSet('', (x for x in xrange(20000) if not x&1))
        all  = DocSet('', (xrange(10000)))
        disp = DocSet('', (xrange(10000, 20000)))
        todd, tall, tdisp1, tdisp2 = 0.0, 0.0, 0.0, 0.0
        for i in range(1000):
            t0 = time()
            odd.combinedCardinality(even)
            todd += time()-t0
            t0 = time()
            all.combinedCardinality(all)
            tall += time()-t0
            t0 = time()
            all.combinedCardinality(disp)
            tdisp1 += time()-t0
            t0 = time()
            disp.combinedCardinality(all)
            tdisp2 += time()-t0
        self.assertTiming(0.020, todd,   0.200)
        self.assertTiming(0.020, tall,   0.100)
        self.assertTiming(0.002, tdisp1, 0.005) # zipper/upper_bound optimization 1
        self.assertTiming(0.002, tdisp2, 0.005) # zipper/upper_bound optimization 2

    def testIncrementalSearch(self):
        all1 = DocSet.forTesting(1000000)
        all2 = DocSet('t0', range(500000-10,500000+10))
        small = DocSet('q', range(500000-10,500000+10))
        t1, t2 = 0, 0
        for i in range(1000):
            t0 = time()
            small.combinedCardinality(all1)
            t1 += time() - t0
            t0 = time()
            small.combinedCardinality(all2)
            t2 += time() - t0
        self.assertTrue( 0.8 < abs(t1/t2) < 1.2, t1/t2 )

    def testSwitchPoint(self):
        # This test is used to tune the selection of intersection algoritms in _docset.cpp
        # For |N| ~ |M|, zipper is the fastest.
        # For |N| >> |M|, incremental search is the fastest
        # SWITCHPOINT = |N| / |M|
        # Run this test for various values of SWITCHPOINT, adjusting SWITCHPOINT here *and*
        # in _docset.cpp.  Look for a minimum.
        nrOfDocs = 20000
        SWITCHPOINT = 100 # 2008/09/18, seems good, EJG
        M = DocSetList()
        for i in xrange(100):
            M.add(DocSet.forTesting(nrOfDocs))
        N1 = DocSet.forTesting(nrOfDocs/SWITCHPOINT)
        N2 = DocSet('', xrange(nrOfDocs-nrOfDocs/SWITCHPOINT, nrOfDocs))
        N3 = DocSet('', sorted(sample(xrange(nrOfDocs), nrOfDocs/SWITCHPOINT)))
        tn1, tn2, tn3 = 0.0, 0.0, 0.0
        for i in range(10):
            for i in xrange(100):
                t0 = time()
                M.termCardinalities(N1).next()
                tn1 += time()-t0
            for i in xrange(100):
                t0 = time()
                M.termCardinalities(N2).next()
                tn2 += time()-t0
            for i in xrange(100):
                t0 = time()
                M.termCardinalities(N3).next() # random, more realistic?
                tn3 += time()-t0
        tn1avg = tn1/10
        tn2avg = tn2/10
        tn3avg = tn3/10
        #print '%d: %.2f, %.2f, %.2f' % (SWITCHPOINT, tn1avg, tn2avg, tn3avg)
        self.assertTiming(0.01, tn1avg, 0.20)
        self.assertTiming(0.01, tn2avg, 0.20)

    def XXXtestMemoryLeaks(self):
        from gc import collect
        self.createBigIndex(9, 2) # 10 records, 6 values
        termEnum = self.reader.terms(Term('field0',''))
        termDocs = self.reader.termDocs()
        dsl = DocSetList.fromTermEnum(termEnum, termDocs)
        print 'repeating fromTermEnum, watch top'
        for j in range(10):
            raw_input('start')
            for i in range(100000):
                termEnum = self.reader.terms(Term('field0',''))
                termDocs = self.reader.termDocs()
                dsl = DocSetList.fromTermEnum(termEnum, termDocs)
            del dsl, termEnum, termDocs
            collect()
            raw_input('done')
        print 'repeating termCardinalities, watch top'
        for i in range(1000000):
            cs = dsl.termCardinalities(DocSet('', [1,2,3,4,5,6,7,8,9]))
        NA = Wildcard()
        self.assertEquals([('t€rm0', NA), ('t€rm1', NA), ('t€rm2', NA)], list(cs))

    def XXXXtestReadRealyBigIndex(self):
        try:
            reader = IndexReader.open('testindexoptff')
        except:
            return
        fields = reader.getFieldNames(IndexReader.FieldOption.ALL)
        termDocs = reader.termDocs()
        terms, postings = 0, 0
        t0 = time()
        dsls = []
        for field in fields:
            #print field,
            stdout.flush()
            termEnum = reader.terms(Term(field,''))
            dsl = DocSetList.fromTermEnum(termEnum, termDocs)
            dsls.append(dsl)
            terms += len(dsl)
        t1 = time()
        postings = sum(sum(len(docset) for docset in dsl) for dsl in dsls)
        #print '%.1f seconds, %.2g documents, %d fields, %d terms, %.2g postings,' % (t1-t0, reader.numDocs(), len(fields), terms, postings),
        #print 'on average %s postings per term.' % (postings/terms),
        #stdout.flush()

# Some tests on Juicer with EduRep 8/2008:
# (1st time)
# 1.8 seconds, 7.1e+05 documents, 194 fields, 30595 terms, 4.4e+06 postings.
# on average 144 postings per term.
# (2nd time)
# 0.8 seconds, 7.1e+05 documents, 194 fields, 30595 terms, 4.4e+06 postings.
# on average 144 postings per term.

# 1G Laptop with testindex (10.000.000 postings!):
# (1st time)
# 9.3(8.7) seconds, 1e+06 documents, 10 fields, 9010 terms, 1e+07 postings.
# on average 1109 postings per term.
# (2nd time)
# 2.9(3.4,2.7,2.6) seconds, 1e+06 documents, 10 fields, 9010 terms, 1e+07 postings.
# on average 1109 postings per term.

# same as above, only with index optimized
# 1.1(1.0) seconds (!!!), 1e+06 documents, 10 fields, 9010 terms, 1e+07 postings.
# on average 1109 postings per term.
