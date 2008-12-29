# -*- encoding: utf-8 -*-
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

from tempfile import mkdtemp, gettempdir
from time import sleep
import os
from os.path import isfile, join
from os import listdir
from shutil import rmtree

from cq2utils import CQ2TestCase, CallTrace

from facetindex import Document, IDFIELD, LuceneIndex2

from meresco.components.lucene import CQL2LuceneQuery
from meresco.components.lucene.cqlparsetreetolucenequery import Composer

from cqlparser import parseString

from PyLucene import Document as PyDocument, Field, IndexReader, IndexWriter, Term, TermQuery, MatchAllDocsQuery, JavaError
from weightless import Reactor

class Lucene2Test(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.timer = CallTrace('timer')
        self._luceneIndex = LuceneIndex2(
            directoryName=self.tempdir,
            timer=self.timer)

        self.timerCallbackMethod = self._luceneIndex._lastUpdateTimeout

    def tearDown(self):
        self._luceneIndex.close()
        CQ2TestCase.tearDown(self)

    def testCreation(self):
        self.assertEquals(os.path.isdir(self.tempdir), True)
        self.assertTrue(IndexReader.indexExists(self.tempdir))

    def testAddToIndex(self):
        myDocument = Document('0123456789')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)
        self.timerCallbackMethod()

        hits = self._luceneIndex.executeQuery(TermQuery(Term('title', 'titel')))
        self.assertEquals(len(hits), 1)
        self.assertEquals(['0123456789'], list(hits))

    def testAddToIndexWithDuplicateField(self):
        myDocument = Document('id')
        myDocument.addIndexedField('title', 'een titel')
        myDocument.addIndexedField('title', 'een sub titel')
        self._luceneIndex.addDocument(myDocument)
        self.timerCallbackMethod()

        hits = self._luceneIndex.executeQuery(TermQuery(Term('title', 'titel')))
        self.assertEquals(len(hits), 1)

        hits = self._luceneIndex.executeQuery(TermQuery(Term('title', 'sub')))
        self.assertEquals(len(hits), 1)

    def testAddTwoDocuments(self):
        myDocument = Document('1')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)

        myDocument = Document('2')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)
        self.timerCallbackMethod()

        hits = self._luceneIndex.executeQuery(TermQuery(Term('title', 'titel')))
        self.assertEquals(2, len(hits))

    def testAddDocumentWithTwoValuesForOneField(self):
        myDocument = Document('1')
        myDocument.addIndexedField('field1', 'value_1')
        myDocument.addIndexedField('field1', 'value_2')
        self._luceneIndex.addDocument(myDocument)

        self.timerCallbackMethod()

        def check(value):
            hits = self._luceneIndex.executeQuery(TermQuery(Term('field1', value)))
            self.assertEquals(1, len(hits))
        check('value_1')
        check('value_2')

    def testAddUTF8Document(self):
        myDocument = Document('0123456789')
        myDocument.addIndexedField('title', 'BijenkorfÂ´s')
        self._luceneIndex.addDocument(myDocument)

    def testAddDocumentWithFailure(self):
        self._luceneIndex.close()
        myIndex = LuceneIndex2(
            directoryName=self.tempdir,
            timer=Reactor())
        class MyException(Exception):
            pass
        myDocument = Document('1')
        myDocument.addIndexedField('aap', 'noot')
        myIndex.addDocument(myDocument)
        def validate():
            raise MyException('Boom')
        myDocument.validate = validate
        try:
            myIndex.addDocument(myDocument)
            self.fail()
        except MyException:
            pass

        my2Document = Document('2')
        my2Document.addIndexedField('aap', 'noot')
        myIndex.addDocument(my2Document)


    def testDeleteFromIndex(self):
        myDocument = Document('1')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)

        myDocument = Document('2')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)
        self.timerCallbackMethod()

        hits = self._luceneIndex.executeQuery(TermQuery(Term('title', 'titel')))
        self.assertEquals(2, len(hits))

        self._luceneIndex.delete('1')

        hits = self._luceneIndex.executeQuery(TermQuery(Term('title', 'titel')))
        self.assertEquals(2, len(hits))

        self.timerCallbackMethod()
        hits = self._luceneIndex.executeQuery(TermQuery(Term('title', 'titel')))
        self.assertEquals(1, len(hits))

    def testAddDeleteWithoutReopenInBetweenIsIllegal(self):
        myDocument = Document('1')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)
        try:
            self._luceneIndex.delete('1')
        except Exception, e:
            self.assertEquals("Document '1' not in index.  Perhaps not flushed?", str(e))

    def testIndexReaderResourceManagementKeepsIndexOpenAndClosesItWhenAllRefsAreGone(self):
        myDocument = Document('0123456789')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)
        self.timerCallbackMethod()
        hits = self._luceneIndex.executeQuery(TermQuery(Term('title', 'titel')))
        # keep ref to hits, while refreshing/reopening the index after timeout
        self.timerCallbackMethod()
        # now try to get the results,
        try:
            list(hits)
        except JavaError, e:
            self.assertEquals('org.apache.lucene.store.AlreadyClosedException: this IndexReader is closed', str(e))
            self.fail('this must not fail on a closed reader')


    def testIndexCloses(self):
        index = LuceneIndex2(self.tempdir + '/x', timer=self.timer)
        myDocument = Document('1')
        myDocument.addIndexedField('title', 'een titel')
        index.addDocument(myDocument)
        # The next call shouldn't be necessary, but ....
        index.__del__()
        index = None
        self.assertFalse(isfile(self.tempdir + '/x/write.lock'))

    def testCQLConversionIntegration(self):
        queryConvertor = CQL2LuceneQuery([])
        queryConvertor.addObserver(self._luceneIndex)
        myDocument = Document('0123456789')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)
        self.timerCallbackMethod()
        hits1 = list(self._luceneIndex.executeQuery(TermQuery(Term('title', 'titel'))))
        hits2 = list(queryConvertor.executeCQL(parseString("title = titel")))
        self.assertEquals(len(hits1), len(hits2))
        self.assertEquals(['0123456789'], hits1)
        self.assertEquals(['0123456789'], hits2)

    def testUpdateSetsTimer(self):
        myDocument = Document('1')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument) # this must trigger a timer
        self.assertEquals('addTimer', self.timer.calledMethods[0].name)
        self.assertEquals(1, self.timer.calledMethods[0].args[0])
        timeCallback = self.timer.calledMethods[0].args[1]
        self.assertTrue(timeCallback)

    def testUpdateRESetsTimer(self):
        self.timer.returnValues['addTimer'] = 'aToken'
        myDocument = Document('1')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument) # this must trigger a timer
        self._luceneIndex.addDocument(myDocument) # this must REset the timer
        self.assertEquals(['addTimer', 'removeTimer', 'addTimer'],
            [method.name for method in self.timer.calledMethods])
        self.assertEquals('aToken', self.timer.calledMethods[1].args[0])

    def testOptimizeOnTimeOut(self):
        self.timer.returnValues['addTimer'] = 'aToken'
        myDocument = Document('1')
        myDocument.addIndexedField('title', 'een titel')
        self._luceneIndex.addDocument(myDocument)
        timeCallback = self.timer.calledMethods[0].args[1]
        self.assertEquals(0, len(list(self._luceneIndex.executeQuery(TermQuery(Term('title', 'titel'))))))
        timeCallback()
        self.assertEquals(1, len(list(self._luceneIndex.executeQuery(TermQuery(Term('title', 'titel'))))))
        # after callback the old timer will not be removed
        self._luceneIndex.addDocument(myDocument)
        self.assertEquals(['addTimer', 'addTimer'],
            [method.name for method in self.timer.calledMethods])

    def testStart(self):
        intercept = CallTrace('Interceptor')
        self._luceneIndex.addObserver(intercept)
        self._luceneIndex.start()
        self.assertEquals(2, len(intercept.calledMethods))
        self.assertEquals('indexStarted', intercept.calledMethods[0].name)
        self.assertEquals('indexStarted', intercept.calledMethods[1].name)
    def testAnalyser(self):
        myDocument = Document('id0')
        myDocument.addIndexedField('field', 'a')
        myDocument.addIndexedField('field', 'vAlUe')
        self._luceneIndex.addDocument(myDocument)
        self.timerCallbackMethod()

        hits = self._luceneIndex.executeQuery(TermQuery(Term('field', 'a')))
        self.assertEquals(len(hits), 1)
        self.assertEquals(['id0'], list(hits))

        hits = self._luceneIndex.executeQuery(TermQuery(Term('field', 'value')))
        self.assertEquals(len(hits), 1)
        self.assertEquals(['id0'], list(hits))

