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
from cq2utils import CQ2TestCase, CallTrace
from PyLucene import IndexWriter, IndexSearcher, StandardAnalyzer, Document, Field, Term, MatchAllDocsQuery, TermQuery, RAMDirectory, QueryFilter, IndexReader
from random import randint
from merescocomponents.facetindex.lucenedocidtracker import LuceneDocIdTracker, LuceneDocIdTrackerException
from glob import glob
from time import time
from cq2utils.profileit import profile
from os import mkdir, listdir
from os.path import join, isdir
from shutil import rmtree

#import sys, os
#sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

def randomSequence(length):
    docs = []
    for n in xrange(100,100+length):
        docs.append(n)
        yield n
        if randint(0,2) == 0: #random delete p = 1/3
            i = randint(0,len(docs)-1)
            yield -docs[i]
            del docs[i]

class LuceneDocIdTrackerTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.writer = IndexWriter(self.tempdir, StandardAnalyzer(), True)
        self.setMergeFactor(2)
        #self.writer.setInfoStream(System.out)

    def setMergeFactor(self, mergeFactor):
        self.writer.setMergeFactor(mergeFactor)
        self.writer.setMaxBufferedDocs(mergeFactor)
        self.tracker = LuceneDocIdTracker(mergeFactor, directory = self.createTrackerDir())

    def testDefaultMergeFactor(self):
        mergeFactor = self.writer.getMergeFactor()
        self.assertEquals(2, mergeFactor)
        self.assertEquals(2, self.writer.getMaxBufferedDocs())

    def testInsertDoc(self):
        doc = Document()
        doc.add(Field('__id__', '1', Field.Store.YES, Field.Index.UN_TOKENIZED))
        self.writer.addDocument(doc)
        self.assertEquals(1, self.writer.docCount())

    def addDoc(self, identifier):
        self.tracker.next()
        doc = Document()
        doc.add(Field('__id__', str(identifier), Field.Store.YES, Field.Index.UN_TOKENIZED))
        self.writer.addDocument(doc)

    def deleteDoc(self, doc):
        self.tracker.flush()
        self.writer.flush()
        hits = IndexSearcher(self.tempdir).search(TermQuery(Term('__id__', str(doc))))
        luceneId = int(list(hits)[0].getId())
        self.tracker.deleteLuceneId(luceneId)
        self.writer.deleteDocuments(Term('__id__', str(doc)))

    def processDocs(self, docs):
        for doc in docs:
            if doc < 0:
                self.deleteDoc(-doc)
            else:
                self.addDoc(doc)

    def findAll(self):
        self.writer.flush()
        self.tracker.flush()
        searcher = IndexSearcher(self.tempdir)
        hits = searcher.search(MatchAllDocsQuery())
        foundIds = [hit.getId() for hit in hits]
        foundDocs = [int(hit.get('__id__')) for hit in hits]
        return foundIds, foundDocs

    def assertMap(self, sequence, luceneIds, foundDocs):
        docs = [doc for doc in sequence if doc >= 0]
        docids = self.tracker.map(luceneIds)
        should = [docs[docid] for docid in docids]
        self.assertEquals(should, foundDocs)

    def testFlushOnEmptyTracker(self):
        self.tracker.flush()

    def testA(self):
        #[100, 101, -101, 102, 103, -102, 104, -100, 105]
        self.processDocs([100, 101])
        self.assertEquals(([0,1], [100,101]), self.findAll())
        self.processDocs([-101]) # lucene write .del file
        self.assertEquals(([0], [100]), self.findAll())
        self.processDocs([102]) # lucene does merge
        self.assertEquals(([0,1], [100,102]), self.findAll())
        self.assertEquals([0,2], list(self.tracker.map([0,1])))
        self.processDocs([103, -102, 104, -100, 105])
        self.assertEquals(([2,3,4], [103,104,105]), self.findAll())
        self.assertEquals([3,4,5], list(self.tracker.map([2,3,4])))

    def testB(self):
        s = [100, 101, -101, 102, 103, 104, -104, 105, 106, 107, 108, -106, 109]
        self.processDocs(s)
        foundIds, foundDocs = self.findAll()
        self.assertEquals([0,1,2,3,5,6,7], foundIds)
        self.assertEquals([100,102,103,105,107,108,109], foundDocs)
        self.assertMap(s, foundIds, foundDocs)

    def testC(self):
        s = [100, 101, 102, 103, 104, 105, -102, 106, 107, 108, 109]
        self.processDocs(s)

        luceneIds, foundDocs = self.findAll()
        self.assertEquals([0,1,2,3,4,5,6,7,8], luceneIds)
        self.assertEquals([100,101,103,104,105,106,107,108,109], foundDocs)
        self.assertMap(s, luceneIds, foundDocs)

    def XXXXXXXXXXXXXXXXXXXXXXXXXXXtestRandom(self):
        mergeFactor = randint(2,50)
        self.setMergeFactor(mergeFactor)
        size = randint(100,1000)
        print 'Testing random sequence of length %d, with mergeFactor %d.' % (size,mergeFactor)
        s = list(randomSequence(size))
        try:
            t0 = time()
            self.processDocs(s)
            print time() - t0, 'seconds'
            self.assertMap(s, *self.findAll())
        except AssertionError:
            name = 'failtestsequences/sequence-%d' % randint(1,2**30)
            f = open(name, 'w')
            f.write('%s\n' % mergeFactor)
            for n in s:
                f.write('%s\n' % n)
            f.close()
            print 'Failed test sequence written to "%s"' % name
            raise

    def testPickupStateFromOptimizedIndex(self):
        s0 = [100, 101, 102]
        self.processDocs(s0)
        self.writer.optimize()
        self.tracker = LuceneDocIdTracker(self.writer.getMergeFactor(), maxDoc=self.writer.docCount(), directory=self.createTrackerDir())
        s1 = [-100, 103, 104, 105, 106]
        self.processDocs(s1)
        foundIds, foundDocs = self.findAll()
        self.assertMap(s0 + s1, foundIds, foundDocs)

    def testPickupStateFromOptimizedIndexAndWriteState(self):
        self.processDocs([100, 101])
        self.writer.optimize()
        self.tracker = LuceneDocIdTracker(self.writer.getMergeFactor(), maxDoc=self.writer.docCount(), directory=self.createTrackerDir())
        self.processDocs([102])
        self.assertEquals(['0.deleted', '0.docids', 'tracker.segments'], sorted(listdir(join(self.tempdir, 'tracker'))))

    def testPickupStateWhereLuceneLeftItOnBiggerScale(self):
        s0 = range(100, 200)
        self.processDocs(s0)
        self.writer.optimize()
        self.tracker = LuceneDocIdTracker(self.writer.getMergeFactor(), maxDoc=self.writer.docCount(), directory=self.createTrackerDir())
        s1 = [-100, 1001, 1002]
        self.processDocs(s1)
        foundIds, foundDocs = self.findAll()
        self.assertMap(s0 + s1, foundIds, foundDocs)

    def testEquals(self):
        mkdir(self.tempdir+'/1')
        mkdir(self.tempdir+'/2')
        self.assertEquals(LuceneDocIdTracker(3, directory='p'), LuceneDocIdTracker(3, directory='x'))
        self.assertNotEquals(LuceneDocIdTracker(2, directory='p'), LuceneDocIdTracker(3, directory='x'))
        t1 = LuceneDocIdTracker(2, directory=self.tempdir+'/1')
        t2 = LuceneDocIdTracker(2, directory=self.tempdir+'/2')
        t1.next() # ramsegments
        self.assertNotEquals(t1, t2)
        t2.next()
        self.assertEquals(t1, t2)
        t1.deleteLuceneId(0)
        self.assertNotEquals(t1, t2)
        t2.deleteLuceneId(0)
        self.assertEquals(t1, t2)
        t1.next() # segments
        self.assertNotEquals(t1, t2)
        t2.next()
        self.assertEquals(t1, t2)

    def testSaveAndLoad(self):
        s0 = [100, 101, 102]
        self.processDocs(s0)
        self.tracker.flush()
        tracker = LuceneDocIdTracker(mergeFactor=2, directory=self.tempdir + "/tracker")
        self.assertEquals(self.tracker, tracker)

    def testFlushOnMergeAndOnCloseJustLikeLucene(self):
        # let both tracker and writer create 1 segment of 100..101 and keep 102 in memory
        self.processDocs([100, 101, 102])
        tracker = LuceneDocIdTracker(mergeFactor=2, directory=self.tempdir + "/tracker")
        hits = IndexSearcher(self.tempdir).search(MatchAllDocsQuery())
        self.assertEquals(2, len(hits))
        self.assertEquals(len(hits), tracker._segmentInfo[0].length)
        self.assertEquals(0, len(tracker._ramSegmentsInfo))

        # let both tracker and writer flush 102 to disk
        self.writer.close()
        self.tracker.close()
        tracker = LuceneDocIdTracker(mergeFactor=2, directory=self.tempdir + "/tracker")
        hits = IndexSearcher(self.tempdir).search(MatchAllDocsQuery())
        self.assertEquals(3, len(hits))
        self.assertEquals(len(hits), tracker._segmentInfo[0].length)
        self.assertEquals(0, len(tracker._ramSegmentsInfo))

    def testFailLoadWhenDataAlreadyInList(self):
        tracker = LuceneDocIdTracker(mergeFactor=2, directory=self.getTrackerDir(), maxDoc=10)
        tracker.next()
        tracker.next()
        tracker.flush()

        try:
            tracker._load()
            self.fail()
        except LuceneDocIdTrackerException, e:
            self.assertEquals('DocIdList not empty on load', str(e))

    def getTrackerDir(self):
        return join(self.tempdir, 'tracker')

    def createTrackerDir(self):
        name = self.getTrackerDir()
        isdir(name) and rmtree(name)
        mkdir(name)
        return name

    def testAddAndFlush(self):
        tracker = LuceneDocIdTracker(10, directory = self.createTrackerDir())
        tracker.next()
        tracker.next()
        tracker.flush()

    def testTrackerSavedDeletesOfOldDocIds(self):
        tracker = LuceneDocIdTracker(2, directory = self.createTrackerDir())
        tracker.next()
        tracker.next()
        tracker.next()
        tracker.next() # generates a merge and a save of segment 0, of size 4
        tracker.next() # creates a second segment, which must be saved properly on deletes
        tracker.next()
        tracker.deleteLuceneId(0) # delete first document in already saved segement 0
        self.assertTrue(tracker.isDeleted(0))
        tracker.close()
        tracker = LuceneDocIdTracker(2, directory = self.getTrackerDir())
        self.assertTrue(tracker.isDeleted(0))

    def testDeletesAreDeletedOnMerge(self):
        """i.e. Delete information is deleted on merge"""
        tracker = LuceneDocIdTracker(mergeFactor=2, directory=self.tempdir + "/tracker")
        for i in range(5):
            tracker.next()
        tracker.deleteLuceneId(0)

        tracker.next()
        tracker.next()
        tracker.flush()

        tracker2 = LuceneDocIdTracker(mergeFactor=2, directory=self.tempdir + "/tracker")
        self.assertEquals(tracker, tracker2)

    def testDelete2LuceneIdsInOneSegment(self):
        tracker = LuceneDocIdTracker(mergeFactor=10, directory=self.tempdir + "/tracker")
        tracker.next()
        tracker.flush()
        tracker.next()
        tracker.flush()
        tracker.deleteLuceneId(1)

        tracker2 = LuceneDocIdTracker(mergeFactor=10, directory=self.tempdir + "/tracker")
        self.assertEquals(tracker, tracker2)

    def testSameProblemSlightlyDifferentAngle(self):
        tracker = LuceneDocIdTracker(mergeFactor=10, directory=self.tempdir + "/tracker")
        tracker.next()
        tracker.flush()
        tracker.next()
        tracker.flush()
        tracker.next()
        tracker.flush()
        tracker.deleteLuceneId(1)

        tracker2 = LuceneDocIdTracker(mergeFactor=10, directory=self.tempdir + "/tracker")
        self.assertEquals(tracker, tracker2)
