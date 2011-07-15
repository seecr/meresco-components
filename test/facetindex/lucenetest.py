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
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
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
from utils import asyncreturn

from tempfile import mkdtemp, gettempdir
from time import sleep
import os
from os.path import isfile, join
from os import listdir
from shutil import rmtree

from meresco.components.facetindex import Document, IDFIELD, LuceneIndex
from meresco.components.facetindex import CQL2LuceneQuery
from meresco.components.facetindex.merescolucene import Field, IndexReader, IndexWriter, Term, TermQuery, MatchAllDocsQuery
from meresco.core import be, Observable

from cqlparser import parseString

from weightless.io import Reactor


class LuceneTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self._luceneIndex = LuceneIndex(directoryName=self.tempdir)

    def tearDown(self):
        self._luceneIndex.close()
        CQ2TestCase.tearDown(self)

    def executeQuery(self, *args, **kwargs):
        return asyncreturn(self._luceneIndex.executeQuery, *args, **kwargs)

    def testCreation(self):
        self.assertEquals(os.path.isdir(self.tempdir), True)
        self.assertTrue(IndexReader.indexExists(self.tempdir))

    def testAddToIndex(self):
        myDocument = Document('0123456789')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)
        self._luceneIndex.commit()
        self.assertEquals(1, self._luceneIndex._writer.numDocs())
        self.assertEquals(1, self._luceneIndex.docCount())

        response = self.executeQuery(TermQuery(Term('title', 'titel')))
        self.assertEquals(1, len(response.hits))
        self.assertEquals(['0123456789'], list(response.hits))

    def testAddToIndexWithDuplicateField(self):
        myDocument = Document('id')
        myDocument.addIndexedField('title', 'een titel')
        myDocument.addIndexedField('title', 'een sub titel')
        self._luceneIndex.addDocument(myDocument)
        self._luceneIndex.commit()

        response = self.executeQuery(TermQuery(Term('title', 'titel')))
        self.assertEquals(len(response.hits), 1)

        response = self.executeQuery(TermQuery(Term('title', 'sub')))
        self.assertEquals(len(response.hits), 1)

    def testAddTwoDocuments(self):
        myDocument = Document('1')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)

        myDocument = Document('2')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)
        self._luceneIndex.commit()

        response = self.executeQuery(TermQuery(Term('title', 'titel')))
        self.assertEquals(2, len(response.hits))

    def testAddDocumentWithTwoValuesForOneField(self):
        myDocument = Document('1')
        myDocument.addIndexedField('field1', 'value_1')
        myDocument.addIndexedField('field1', 'value_2')
        self._luceneIndex.addDocument(myDocument)

        self._luceneIndex.commit()

        def check(value):
            response = self.executeQuery(TermQuery(Term('field1', value)))
            self.assertEquals(1, len(response.hits))
        check('value_1')
        check('value_2')

    def testAddUTF8Document(self):
        myDocument = Document('0123456789')
        myDocument.addIndexedField('title', 'BijenkorfÂ´s')
        self._luceneIndex.addDocument(myDocument)

    def testAddDocumentWithFailure(self):
        drilldown = CallTrace('Drilldown')
        self._luceneIndex.addObserver(drilldown)
        class MyException(Exception):
            pass
        myDocument = Document('1')
        myDocument.addIndexedField('aap', 'noot')
        def validate():
            raise MyException('Boom')
        myDocument.validate = validate
        try:
            self._luceneIndex.addDocument(myDocument)
            self.fail()
        except MyException:
            pass
        self._luceneIndex.rollback()

        my2Document = Document('2')
        my2Document.addIndexedField('aap', 'noot')
        self._luceneIndex.addDocument(my2Document)
        self._luceneIndex.commit()
        addDocumentMethods = [m for m in drilldown.calledMethods if m.name=='addDocument']
        self.assertEquals(1, len(addDocumentMethods))
        docId = addDocumentMethods[0].kwargs['docId']
        self.assertEquals(my2Document.docId, docId)
        self.assertEquals([docId], list(self._luceneIndex.docsetFromQuery(MatchAllDocsQuery())))

    def addDocument(self, identifier, **fields):
        doc = Document(identifier)
        for key, value in fields.items():
            doc.addIndexedField(key, value)
        self._luceneIndex.addDocument(doc)

    def testDeleteFromIndex(self):
        self.addDocument('1', title='een titel')
        self.addDocument('2', title='een titel')
        self._luceneIndex.commit()

        response = self.executeQuery(TermQuery(Term('title', 'titel')))
        self.assertEquals(2, len(response.hits))

        self._luceneIndex.delete('1')

        response = self.executeQuery(TermQuery(Term('title', 'titel')))
        self.assertEquals(2, len(response.hits))

        self._luceneIndex.commit()
        response = self.executeQuery(TermQuery(Term('title', 'titel')))
        self.assertEquals(1, len(response.hits))

    def testAddDeleteWithoutCommitInBetween(self):
        drilldown = CallTrace('drilldown')
        self._luceneIndex.addObserver(drilldown)
        self.addDocument('1', exists='true')
        self._luceneIndex.delete('1')
        self._luceneIndex.commit()
        response = self.executeQuery(TermQuery(Term('exists', 'true')))
        self.assertEquals(0, len(response.hits))
        #self.assertEquals(0, self._luceneIndex._tracker.nrOfDocs())
        for i in range(100):
            self.addDocument('%s' % (i+1), exists='true')
        self._luceneIndex.commit()
        self.assertEquals('addDocument', drilldown.calledMethods[-1].name)
        self.assertEquals(['100'], drilldown.calledMethods[-1].kwargs['docDict']['__id__'])
        self.assertEquals(100, drilldown.calledMethods[-1].kwargs['docId'])

        hits = self._luceneIndex._searcher.search(TermQuery(Term('__id__', '100')))
        self.assertEquals(1, hits.length())
        self.assertEquals(100, self._luceneIndex._lucene2docId[hits.id(0)])
        

    def testIndexReaderResourceManagementKeepsIndexOpenAndClosesItWhenAllRefsAreGone(self):
        myDocument = Document('0123456789')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)
        self._luceneIndex.commit()
        response = self.executeQuery(TermQuery(Term('title', 'titel')))
        # keep ref to response.hits, while refreshing/reopening the index after timeout
        self._luceneIndex.commit()
        # now try to get the results,
        try:
            list(response.hits)
        except JavaError, e:
            print str(e)
            self.assertEquals('org.apache.lucene.store.AlreadyClosedException: this IndexReader is closed', str(e))
            self.fail('this must not fail on a closed reader')

    def testIndexCloses(self):
        index = LuceneIndex(self.tempdir + '/x')
        myDocument = Document('1')
        myDocument.addIndexedField('title', 'een titel')
        index.addDocument(myDocument)
        # The next call shouldn't be necessary, but ....
        index.__del__()
        index = None
        self.assertFalse(isfile(self.tempdir + '/x/write.lock'))

    def testCQLConversionIntegration(self):
        class MockSruHandler(Observable):
            def executeQuery(self, query):
                response = yield self.asyncany.executeQuery(cqlAbstractSyntaxTree=query)
                raise StopIteration(response)

        dna = be(
            (Observable(), 
                (MockSruHandler(),
                    (CQL2LuceneQuery([('a',1)]),
                        (self._luceneIndex,)
                    )
                )
            )
        )
        
        myDocument = Document('0123456789')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)
        self._luceneIndex.commit()
        response1 = self.executeQuery(TermQuery(Term('title', 'titel')))
        response2 = asyncreturn(dna.asyncany.executeQuery, parseString("title = titel"))
        self.assertEquals(len(response1.hits), len(response2.hits))
        self.assertEquals(['0123456789'], response1.hits)
        self.assertEquals(['0123456789'], response2.hits)

    def testObserverInit(self):
        intercept = CallTrace('Interceptor')
        self._luceneIndex.addObserver(intercept)

        self._luceneIndex.observer_init()

        self.assertEquals(1, len(intercept.calledMethods))
        self.assertEquals('indexStarted', intercept.calledMethods[0].name)

    def testAddIsAlsoDeleteCausesBug(self):
        reopen = self._luceneIndex._reopenIndex
        self._luceneIndex._reopenIndex = lambda: None

        def add(value):
            doc = Document("theIdIsTheSame")
            doc.addIndexedField('value', value)
            self._luceneIndex.addDocument(doc)

        for i in range(100):
            add("a" + str(i))
            reopen()

    def testAddingSameIdentifierInOneBatch(self):
        def add(value):
            doc = Document("theIdIsTheSame")
            doc.addIndexedField('value', value)
            self._luceneIndex.addDocument(doc)
        delete = lambda : self._luceneIndex.delete('theIdIsTheSame')
        observer = CallTrace('observer')
        add('1')
        self._luceneIndex.commit()
        self._luceneIndex.addObserver(observer)
        response = self.executeQuery(TermQuery(Term('__id__', 'theIdIsTheSame')))
        self.assertEquals(1, response.total)

        add('2')
        add('3')
        self._luceneIndex.commit()
        response = self.executeQuery(TermQuery(Term('__id__', 'theIdIsTheSame')))
        self.assertEquals(1, response.total)
        self.assertEquals(['deleteDocument', 'addDocument', 'deleteDocument', 'addDocument'], [m.name for m in observer.calledMethods])
        self.assertEquals([0,1,1,2], [m.kwargs['docId'] for m in observer.calledMethods])

    def testAddingAndDeletingInSameBatch(self):
        def add(value):
            doc = Document("theIdIsTheSame")
            doc.addIndexedField('value', value)
            self._luceneIndex.addDocument(doc)
        delete = lambda : self._luceneIndex.delete('theIdIsTheSame')
        observer = CallTrace('observer')
        add('1')
        self._luceneIndex.commit()
        self._luceneIndex.addObserver(observer)

        
        add('2')
        delete()
        self._luceneIndex.commit()
        response = self.executeQuery(TermQuery(Term('__id__', 'theIdIsTheSame')))
        self.assertEquals(0, response.total)

        self.assertEquals(['deleteDocument', 'addDocument', 'deleteDocument'], [m.name for m in observer.calledMethods])
        self.assertEquals([0,1,1], [m.kwargs['docId'] for m in observer.calledMethods])

    def testAddingAddingAndDeletingInSameBatch(self):
        def add(value):
            doc = Document("theIdIsTheSame")
            doc.addIndexedField('value', value)
            self._luceneIndex.addDocument(doc)
        delete = lambda : self._luceneIndex.delete('theIdIsTheSame')
        observer = CallTrace('observer')
        add('1')
        self._luceneIndex.commit()
        self._luceneIndex.addObserver(observer)

        add('2')
        add('3')
        delete()
        self._luceneIndex.commit()
        response = self.executeQuery(TermQuery(Term('__id__', 'theIdIsTheSame')))
        self.assertEquals(0, response.total)

        self.assertEquals(['deleteDocument', 'addDocument', 'deleteDocument', 'addDocument', 'deleteDocument'], [m.name for m in observer.calledMethods])
        self.assertEquals([0,1,1,2,2], [m.kwargs['docId'] for m in observer.calledMethods])

    def testAddingDeletingAddingInSameBatch(self):
        def addSameDoc():
            doc = Document("theIdIsTheSame")
            doc.addIndexedField('value', 'value')
            self._luceneIndex.addDocument(doc)
        deleteSameDoc = lambda : self._luceneIndex.delete('theIdIsTheSame')
        observer = CallTrace('observer')
        addSameDoc()
        self._luceneIndex.commit()
        self._luceneIndex.addObserver(observer)
        addSameDoc()
        deleteSameDoc()
        addSameDoc()
        self._luceneIndex.commit()
        response = self.executeQuery(TermQuery(Term('__id__', 'theIdIsTheSame')))
        self.assertEquals(1, response.total)
        self.assertEquals(response.total, self._luceneIndex._currentTracker.nrOfDocs())
        methodNames = [m.name for m in observer.calledMethods]
        docIds = [m.kwargs['docId'] for m in observer.calledMethods]
        self.assertEquals((['deleteDocument','addDocument','deleteDocument','addDocument',],[0,1,1,2]), (methodNames, docIds))

    def testMultipleAddsWithoutReopenIsEvenDifferent(self):
        reopen = self._luceneIndex._reopenIndex
        self._luceneIndex._reopenIndex = lambda: None

        def add(value):
            doc = Document("theIdIsTheSame")
            doc.addIndexedField('value', value)
            self._luceneIndex.addDocument(doc)

        for i in range(100):
            add("a" + str(i))

        reopen()

    def testAnalyzer(self):
        myDocument = Document('id0')
        myDocument.addIndexedField('field', 'a')
        myDocument.addIndexedField('field', 'vAlUe')
        self._luceneIndex.addDocument(myDocument)
        self._luceneIndex.commit()

        response = self.executeQuery(TermQuery(Term('field', 'a')))
        self.assertEquals(1, response.total)
        self.assertEquals(1, len(response.hits))
        self.assertEquals(['id0'], list(response.hits))

        response = self.executeQuery(TermQuery(Term('field', 'value')))
        self.assertEquals(len(response.hits), 1)
        self.assertEquals(['id0'], list(response.hits))

    def testSorting(self):
        myDocument = Document('id0')
        myDocument.addIndexedField('field1', 'one')
        myDocument.addIndexedField('field2', 'a')
        self._luceneIndex.addDocument(myDocument)
        myDocument = Document('id1')
        myDocument.addIndexedField('field1', 'one')
        myDocument.addIndexedField('field2', 'b')
        self._luceneIndex.addDocument(myDocument)
        self._luceneIndex.commit()

        response = self.executeQuery(TermQuery(Term('field1', 'one')), sortBy='field2', sortDescending=False)
        self.assertEquals(len(response.hits), 2)
        self.assertEquals(['id0', 'id1'], list(response.hits))

        response = self.executeQuery(TermQuery(Term('field1', 'one')), sortBy='field2', sortDescending=True)
        self.assertEquals(len(response.hits), 2)
        self.assertEquals(['id1', 'id0'], list(response.hits))

    def testSortingNonExistingField(self):
        myDocument = Document('id0')
        myDocument.addIndexedField('field1', 'one')
        self._luceneIndex.addDocument(myDocument)
        myDocument = Document('id1')
        myDocument.addIndexedField('field1', 'one')
        self._luceneIndex.addDocument(myDocument)
        self._luceneIndex.commit()

        response = self.executeQuery(TermQuery(Term('field1', 'one')), sortBy='doesNotExist', sortDescending=False)
        self.assertEquals(len(response.hits), 2)
        self.assertEquals(['id0', 'id1'], list(response.hits))

    def testStartAndStopArguments(self):
        def addDoc(n):
            doc = Document(str(n))
            doc.addIndexedField('field', str(n))
            self._luceneIndex.addDocument(doc)
        for n in range(20):
            addDoc(n)
        self._luceneIndex.commit()
        response = self.executeQuery(MatchAllDocsQuery(), 3, 7)
        self.assertEquals(7-3, len(response.hits))
        self.assertEquals(['3', '4', '5', '6'], response.hits)

    def testFilter(self):
        for n in range(30):
            doc = Document(str(n))
            doc.addIndexedField('field', str(n))
            if n < 20:
                doc.addIndexedField('findable', 'true')
            self._luceneIndex.addDocument(doc)

        self._luceneIndex.commit()
        filter = [3, 4, 5, 9, 11, 12, 13]

        response = self.executeQuery(TermQuery(Term('findable', 'true')), docfilter=[])
        self.assertEquals([], response.hits)
        self.assertEquals(0, response.total)

        response = self.executeQuery(TermQuery(Term('findable', 'true')), docfilter=filter)
        self.assertEquals([str(i) for i in filter if i < 20], response.hits)
        self.assertEquals(7, response.total)

        response = self.executeQuery(TermQuery(Term('findable', 'true')), 2, 5, docfilter=filter)
        self.assertEquals(5-2, len(response.hits))
        self.assertEquals([str(i) for i in filter if i < 20][2:5], response.hits)
        self.assertEquals(7, response.total)

    def testFailureRollsBack(self):
        self.addDocument('1', field1='ape')
        try:
            self.addDocument('id')
            self.fail()
        except Exception, e:
            self.assertEquals("Empty document", str(e))
        self.addDocument('2', field1='nut')
        self._luceneIndex.commit()
        self.assertEquals(1, self._luceneIndex.docCount())

    def testPassOnAddDocumentForDocumentNotInIndexSoDeleteIsIgnored(self):
        observer = CallTrace('observer')
        self._luceneIndex.addObserver(observer)
        self.addDocument('2', field1='nut')
        self.assertEquals(1, len(observer.calledMethods))
        self.assertEquals(1, len(self._luceneIndex._commandQueue))
        self.assertEquals("addDocument", observer.calledMethods[0].name)
        self.assertEquals({'docDict': {u'field1': [u'nut'], u'__id__': [u'2']}, 'docId': 0}, observer.calledMethods[0].kwargs)

    def testPassOnDeleteDocument(self):
        observer = CallTrace('observer')
        self._luceneIndex.addObserver(observer)
        self.addDocument('identifier', field0='term0') # 0
        self._luceneIndex.delete('identifier')
        self.assertEquals("addDocument", observer.calledMethods[0].name)
        self.assertEquals({'docDict':{u'field0': [u'term0'], u'__id__': [u'identifier']}, 'docId':0}, observer.calledMethods[0].kwargs)
        self.assertEquals('deleteDocument(docId=0)', str(observer.calledMethods[1]))

    def testDocIdTrackerIntegration(self):
        observer = CallTrace('observer')
        self._luceneIndex.addObserver(observer)
        self.addDocument('a', field0='term0')
        self.addDocument('b', field0='term0')
        self._luceneIndex.delete('a')
        self._luceneIndex.commit()
        self.addDocument('c', field0='term0')
        self.assertEquals(2, observer.calledMethods[-1].kwargs['docId'])

    def testDocSetMapping(self):
        self.addDocument('1', field0='term0')
        self.addDocument('2', field0='term0')
        self.addDocument('3', field0='term0')
        self._luceneIndex.commit()
        result = self._luceneIndex.docsetFromQuery(MatchAllDocsQuery())
        self.assertEquals([0,1,2], list(result))
        self._luceneIndex.delete('2')
        self._luceneIndex.commit()
        result = self._luceneIndex.docsetFromQuery(MatchAllDocsQuery())
        self.assertEquals([0,2], list(result))
        self.addDocument('2', field0='term0')
        self._luceneIndex.commit()
        result = self._luceneIndex.docsetFromQuery(MatchAllDocsQuery())
        self.assertEquals([0,2,3], list(result))
        self.addDocument('1', field0='term0')
        self.addDocument('2', field0='term0')
        self.addDocument('3', field0='term0')
        self._luceneIndex.commit()
        result = self._luceneIndex.docsetFromQuery(MatchAllDocsQuery())
        self.assertEquals([4,5,6], list(result))

    def testDelete(self):
        self.addDocument('1', field0='term0')
        self.addDocument('2', field0='term0')
        self.addDocument('3', field0='term0')
        self._luceneIndex.commit()
        self._luceneIndex.delete('2')
        result = self._luceneIndex.docsetFromQuery(MatchAllDocsQuery())
        self.assertEquals([0,1,2], list(result))
        self._luceneIndex.commit()
        result = self._luceneIndex.docsetFromQuery(MatchAllDocsQuery())
        self.assertEquals([0,2], list(result))

    def testCommitWithoutAddDocumentDoesNotReindex(self):
        reopenIndexCalled = []
        def reopenIndex():
            reopenIndexCalled.append(True)
        self._luceneIndex._reopenIndex = reopenIndex
        self._luceneIndex.commit()
        self.assertEquals([], reopenIndexCalled)

    def testDebugLog(self):
        logfilename = join(self.tempdir, 'logfilename')
        self._luceneIndex.close()
        self._luceneIndex = LuceneIndex(directoryName=join(self.tempdir, 'index'), debugLogFilename=logfilename)
        self.addDocument('1', field0='value0')
        self.addDocument('2', field0='value0')
        self._luceneIndex.delete('3')
        self.addDocument('4', field0='value0')
        self._luceneIndex.commit()
        self._luceneIndex._debugLog.flush()
        self.assertEqualsWS("""# Debug Log for LuceneIndex
# directoryName = '%s/index'
# transactionName = None
+1
+2
-3
+4
=
""" % self.tempdir, open(logfilename).read())

    def testDeleteMultipleOccurrencesOfIdentifier(self):
        document = Document('identifier')
        document.addIndexedField('field', 'value')

        document.addToIndexWith(self._luceneIndex._writer)
        document.addToIndexWith(self._luceneIndex._writer)  # should not happen in practice, but has been seen to happen as the result of historical bug
        self._luceneIndex._writer.optimize()
        self._luceneIndex.close()

        self._luceneIndex = LuceneIndex(directoryName=self.tempdir)

        response = self.executeQuery(MatchAllDocsQuery())
        self.assertEquals(2, response.total)

        self._luceneIndex.delete('identifier')
        self._luceneIndex.commit()

        response = self.executeQuery(MatchAllDocsQuery())
        self.assertEquals(0, response.total)
        self.assertEquals(0, self._luceneIndex._currentTracker.nrOfDocs())

    def testAssertionErrorInCaseTrackerOutOfSync(self):
        from meresco.components.facetindex.lucenedocidtracker import LuceneDocIdTracker
        mergeFactor = self._luceneIndex.getMergeFactor()

        document = Document('identifier')
        document.addIndexedField('field', 'value')
        document.addToIndexWith(self._luceneIndex._writer)
        document.addToIndexWith(self._luceneIndex._writer)

        self._luceneIndex.close()
        outOfSyncTracker = LuceneDocIdTracker(mergeFactor, directory=self.tempdir, maxDoc=1)
        outOfSyncTracker.flush()
        try:
            luceneIndex = LuceneIndex(directoryName=self.tempdir)
        except AssertionError, e:
            self.assertEquals("The docId tracker for the Lucene index in '%s' is out of sync (probably after a crash); Please optimize the index before restarting." % self.tempdir, str(e))
        else:
            self.fail("should have resulted in AssertionError")


