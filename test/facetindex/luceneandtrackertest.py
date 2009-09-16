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

from tempfile import mkdtemp, gettempdir
from time import sleep
import os
from os.path import isfile, join
from os import listdir
from shutil import rmtree

from cq2utils import CQ2TestCase, CallTrace
from merescocomponents.facetindex import Document, IDFIELD, LuceneIndex

from merescocomponents.facetindex import CQL2LuceneQuery

from cqlparser import parseString

from PyLucene import Document as PyDocument, Field, IndexReader, IndexWriter, Term, TermQuery, MatchAllDocsQuery, JavaError
from weightless import Reactor

class LuceneAndTrackerTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        observer = CallTrace('observer')
        observer.addDocument = self.drilldownAddDocument
        observer.deleteDocument = self.drilldownDeleteDocument
        self._luceneIndex = LuceneIndex(directoryName=self.tempdir)
        self._luceneIndex.addObserver(observer)
        self.identifier2docId = {}
        self.deletedDocIds = []
 
    def tearDown(self):
        self._luceneIndex.close()
        CQ2TestCase.tearDown(self)
 
    def drilldownAddDocument(self, docId, docDict):
        identifier = docDict['__id__'][0]
        if self.identifier2docId.has_key(identifier):
            oldDocId = self.identifier2docId[identifier]
            self.assertTrue(oldDocId in self.deletedDocIds, "%s not in %s" %(oldDocId, self.deletedDocIds))
        self.identifier2docId[identifier] = docId
 
    def drilldownDeleteDocument(self, docId):
        self.deletedDocIds.append(docId)
 
    def addDocument(self, identifierNumber):
        doc = Document("%03d" % identifierNumber)
        doc.addIndexedField('field', 'needs value')
        self._luceneIndex.addDocument(doc)
 
    def delete(self, identifier):
        self._luceneIndex.delete(identifier)
 
    def commit(self):
        self._luceneIndex.commit()
 
    def assertLuceneIdsAndDocIds(self):
        docIdAndLuceneId = []
 
        for identifier, docId in self.identifier2docId.items():
            realLuceneId = self._luceneIndex._luceneIdForIdentifier(identifier)
            docIdAndLuceneId.append((docId, realLuceneId, identifier))
        self.assertEquals(len(self.identifier2docId), len(docIdAndLuceneId))
        trackerDocIds = [i for i in self._luceneIndex._tracker._docIds]
        for docId, realLuceneId, identifier in docIdAndLuceneId:
            #print 'identifier', identifier, 'docId', docId, 'realLuceneId', realLuceneId
            docIdAccording2Tracker = self._luceneIndex._tracker.mapLuceneId(realLuceneId)
            #print "docId", docId, docIdAccording2Tracker
            luceneIdAccording2Tracker = trackerDocIds.index(docId)
            #print "luceneId", realLuceneId, luceneIdAccording2Tracker
            self.assertEquals(docId, docIdAccording2Tracker)
            self.assertEquals(realLuceneId, luceneIdAccording2Tracker)
 
    def testDocIdTrackerMismatch(self):
        for i in range(51):
            self.addDocument(i)
        self.commit()
        newDocuments = range(100, 124)
        existingDocuments = range(17)
        for i in newDocuments + existingDocuments:
            self.addDocument(i)

    #TODO:
    # mapDocId, what happens with bisect and -1 in docIds ?? (in tracker code)
