
from cq2utils import CQ2TestCase, CallTrace
from time import time
from merescocomponents.facetindex import LuceneIndex, Document
from merescocomponents.facetindex.tools import unlock
from merescocomponents.facetindex.document import IDFIELD
from PyLucene import MatchAllDocsQuery, Sort
from shutil import rmtree

class OaiUniqueTimeStampTest(CQ2TestCase):
    def testOne(self):
        size = 1000000
        indexDir = 'testindexes/oaiunique%s' % size
        unlock(indexDir)
        index = LuceneIndex(indexDir, timer=CallTrace('timer'))
        if index.docCount() != size:
            print '(Re)Creating index for OaiUniqueTimeStampTest'
            rmtree(indexDir)
            index = LuceneIndex('testindexes/oaiunique', timer=CallTrace('timer'))
            trecreate = time()
            for i in xrange(size):
                doc = Document('id:%s' % i)
                doc.addIndexedField('timestamp', '%.8f' % time(), tokenize=False, store=True)
                index.addDocument(doc)
                if i % 1000 == 0:
                    print 'record', i
            
            index._lastUpdateTimeout()
            print 'recreateTime:', (time() - trecreate)*1000.0, 'ms'

        t0 = time()
        hits = index._searcher.search(MatchAllDocsQuery(), Sort('timestamp', True))
        t1 = time()
        start = 0
        stop = start+200
        recordAndStamps = [(hits[i].get(IDFIELD), hits[i]) for i in range(start,min(len(hits),stop))]
        
        print 'search:', (t1 - t0)*1000.0, 'ms'
        print 'search200:', (time() - t1)*1000.0, 'ms'

        