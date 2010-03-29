#!/usr/local/bin/python
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
from sys import stdout
import os
from time import time, sleep
from random import random, randint, sample
from os.path import join

from merescocomponents.facetindex import DocSetList, DocSet, Trie, IntegerList, LuceneIndex, Document
from merescocomponents.facetindex.merescolucene import Term, IndexReader, asFloat, iterJ
from lucenetestcase import LuceneTestCase
from cq2utils import CallTrace

class PerformanceTuningTest(LuceneTestCase):

    def testRawZipperSpeed(self):
        ds0 = DocSet.forTesting(10000000) # both continous ranges triggers Zipper
        ds1 = DocSet.forTesting(10000000)
        t0 = time()
        ds0.combinedCardinality(ds1)
        self.assertTiming(0.02, time() - t0, 0.05)

    def testStayWithSearch(self):
        ds0 = DocSet.forTesting(10000000)  # one continous (large)
        ds1 = DocSet(xrange(0,  10000000,1000)) # much smaller: triggers Search
        t1 = 0.0
        for i in range(100):
            t0 = time()
            ds0.combinedCardinality(ds1)
            t1 += time() - t0
        self.assertTiming(0.5, t1, 0.9)

    def testSwitchFromSearchToZipperPoint(self):
        t = {}
        ds0 = DocSet.forTesting(10000000)  # one continous (large)
        for interval in [1, 10, 100, 1000, 10000]:
            ds1 = DocSet(xrange(0,10000000, interval)) # much smaller: triggers Search
            t0 = time()
            ds0.combinedCardinality(ds1)
            t[interval] = time() - t0
        # These values are measured by varying SWITCHPOINT: 200 seems optimal
        self.assertTiming(0.0100, t[1]    , 0.0500)
        self.assertTiming(0.0040, t[10]   , 0.0200)
        self.assertTiming(0.0100, t[100]  , 0.0500)
        self.assertTiming(0.0060, t[1000] , 0.0300)
        self.assertTiming(0.0004, t[10000], 0.0020)

    def testWithLotsOfData(self):
        words = 'words'
        totalLength = 0
        trie = Trie()
        t_addvalue = 0
        t_getvalue = 0
        t_getterm = 0
        for i, word in enumerate(word.strip() for word in open(words)):
            if word:
                if type(word) == unicode:
                    word = word.encode('utf-8')
                totalLength += len(word)
                t0 = time()
                trie.add(i, word)
                t_addvalue += time() - t0

        for i, word in enumerate(word.strip() for word in open(words)):
            if word:
                if type(word) == unicode:
                    word = word.encode('utf-8')
                t0 = time()
                resultValue = trie.getValue(word)
                t_getvalue += time() - t0
                self.assertEquals(i, resultValue, (i, resultValue, word))

                #t0 = time()
                #resultTerm = trie.getTerm(i)
                #t_getterm += time() - t0
                #self.assertEquals(word, resultTerm, (i, word, resultTerm))


        print
        print '------- Trie Test Results ----------'
        print 'Words:', i
        print 'Total size:', totalLength, '(%.2f MB)' % (totalLength/1024.0/1024.0)
        print 'Average word size:', totalLength/i, 'characters'
        print 'Time for', i, 'addValue:', t_addvalue, '(', 10**6*t_addvalue/i, 'us)'
        #print 'Time for', i, 'getTerms:', t_getterm , '(', 10**6*t_getterm /i, 'us)'
        print 'Time for', i, 'getValue:', t_getvalue, '(', 10**6*t_getvalue/i, 'us)'
        trie.nodecount()

    def testReadLuceneDocsSpeed(self):
        mapping = IntegerList(10000)
        self.createSimpleIndexWithEmptyDocuments(10000)
        t = 0.0
        for i in range(100):
            t0 = time()
            ds = DocSet.fromQuery(self.searcher, self.matchAllDocsQuery, mapping)
            t += time() - t0
        self.assertTiming(0.05, t, 0.2)  # in ~milliseconds!
        self.assertEquals(range(10000), list(iter(ds)))

    def testVariousCornerCases(self):
        odd  = DocSet((x for x in xrange(20000) if     x&1))
        even = DocSet((x for x in xrange(20000) if not x&1))
        all  = DocSet((xrange(10000)))
        disp = DocSet((xrange(10000, 20000)))
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
        self.assertTiming(0.020, tall,   0.200)
        self.assertTiming(0.002, tdisp1, 0.005) # zipper/upper_bound optimization 1
        self.assertTiming(0.002, tdisp2, 0.005) # zipper/upper_bound optimization 2

    def testNoMemoryLeaksInTermCardinalities(self):
        self.createBigIndex(9, 2, indexName='testMemoryLeaks') # 10 records, 6 values
        dsl = DocSetList.forField(self.reader, 'field0')
        for i in range(100000):
            cs = dsl.termCardinalities(DocSet([1,2,3,4,5,6,7,8,9])).next()
        self.assertNoMemoryLeaks(bandwidth=0.9)

    def testPerformanceOfDocSetListForField(self):
        self.createBigIndex(size=10000, indexName='testIndex0')
        t = 0.0
        for n in range(10):
            for field in iterJ(self.reader.getFieldNames(IndexReader.FieldOption.ALL)):
                t0 = time()
                dsl = DocSetList.forField(self.reader, field)
                t += time() - t0
            self.assertNoMemoryLeaks()
        self.assertTiming(0.05, t/n, 0.20)

    def XXXXtestReadRealyBigIndex(self):
        try:
            reader = IndexReader.open('testindexoptff')
        except:
            return
        fields = reader.getFieldNames(IndexReader.FieldOption.ALL)
        terms, postings = 0, 0
        t0 = time()
        dsls = []
        for field in fields:
            #print field,
            stdout.flush()
            dsl = DocSetList.forField(self.reader, field)
            dsls.append(dsl)
            terms += len(dsl)
        t1 = time()
        postings = sum(sum(len(docset) for docset in dsl) for dsl in dsls)
        #print '%.1f seconds, %.2g documents, %d fields, %d terms, %.2g postings,' % (t1-t0, reader.numDocs(), len(fields), terms, postings),
        #print 'on average %s postings per term.' % (postings/terms),
        #stdout.flush()

    def XXXXXXXtestLucene(self):

        ts = []
        print self.tempdir
        index = LuceneIndex(self.tempdir)
        index._tracker = CallTrace()
        index._tracker.next = xrange(1000000).__iter__().next
        for x in range(1000):
            t0 = time()
            i = 0
            for y in range(100):
                doc = Document(str(x * 1000 + y))
                doc.addIndexedField('term0', 'value0')
                index.addDocument(doc)
                i += len(os.listdir(self.tempdir))
                index.commit()

            t1 = time()
            ts.append(t1 - t0)
            print ts[-1], i, ts[-1] / i * 100
            stdout.flush()

        #print ts


    def XXXXXXXXXtestBaseLucenePerformanceWithVaryingBatchSize(self):
        timings = {}
        print
        for batchsize in [1, 10, 100, 1000]:
            print 'batch', batchsize
            index = LuceneIndex(join(self.tempdir, 'batch_%s' % batchsize))
            t0 = time()
            for docid in range(1000):
                for field, term in (('field%d'%n, 'term%d'%n) for n in xrange(10)):
                    doc = Document('__doc%s__'%docid)
                    doc.addIndexedField(field, term)
                    index.addDocument(doc)
                if docid % batchsize == 0:
                    print 'commit'
                    index.commit()
            index.commit()
            t1 = time() - t0
            timings[batchsize] = t1
            print timings
        print timings

    def testLoadAndSaveSpeed(self):
        l = IntegerList(10**6)
        l1 = IntegerList()
        t0 = time()
        l.save(self.tempdir+'/list.bin')
        t1 = time()
        l1.extendFrom(self.tempdir+'/list.bin')
        t2 = time()
        tsave = t1 - t0
        tload = t2 - t1
        self.assertTiming(0.004, tsave, 0.020)
        self.assertTiming(0.10, tload, 0.50)


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
