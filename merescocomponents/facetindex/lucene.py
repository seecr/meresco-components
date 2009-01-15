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

from os.path import isdir, isfile, join
from os import makedirs
from PyLucene import IndexReader, IndexWriter, IndexSearcher, StandardAnalyzer, Term, TermQuery, Sort,  StandardTokenizer, StandardFilter, LowerCaseFilter, QueryFilter
from time import time

from document import IDFIELD
from merescocore.framework import Observable

from docset import DocSet
from functioncommand import FunctionCommand
from lucenedocidtracker import LuceneDocIdTracker

class LuceneException(Exception):
    pass

class IncludeStopWordAnalyzer(object):
    def tokenStream(self, fieldName, reader):
        return LowerCaseFilter(StandardFilter(StandardTokenizer(reader)))

class LuceneIndex(Observable):

    def __init__(self, directoryName, *ditwilikniet, **ditookniet):
        self._searcher = None
        self._reader = None
        self._writer = None
        Observable.__init__(self)
        self._documentQueue = []
        self._directoryName = directoryName
        if not isdir(self._directoryName):
            makedirs(self._directoryName)
        self._reopenIndex()
        optimized = self.isOptimized()
        assert isfile(join(directoryName, 'tracker.segments')) or optimized, 'index must be optimized or tracker state must be present in directory'
        mergeFactor = self.getMergeFactor()
        maxBufferedDocs = self.getMaxBufferedDocs()
        assert mergeFactor == maxBufferedDocs, 'mergeFactor != maxBufferedDocs'
        self._tracker = LuceneDocIdTracker(self.getMergeFactor(), directory=self._directoryName)

    def _reopenIndex(self):
        if self._writer:
            self._writer.close()
        self._writer = IndexWriter(
            self._directoryName,
            IncludeStopWordAnalyzer(), not IndexReader.indexExists(self._directoryName))
        if self._reader:
            self._reader.close()
        self._reader = IndexReader.open(self._directoryName)
        if self._searcher:
            self._searcher.close()
        self._searcher = IndexSearcher(self._reader)
        self._existingFieldNames = self._reader.getFieldNames(IndexReader.FieldOption.ALL)
        self.do.indexStarted(self._reader)

    def observer_init(self):
        self.do.indexStarted(self._reader)

    def docsetFromQuery(self, pyLuceneQuery):
        t0 = time()
        try:
            return DocSet.fromQuery(self._searcher, pyLuceneQuery)
        finally:
            print 'docsetFromQuery (ms): ', (time()-t0)*1000

    def executeQuery(self, pyLuceneQuery, start=0, stop=10, sortBy=None, sortDescending=None):
        sortField = self._getPyLuceneSort(sortBy, sortDescending)
        if sortField:
            hits = self._searcher.search(pyLuceneQuery, sortField)
        else:
            hits = self._searcher.search(pyLuceneQuery)
        return len(hits), [hits[i].get(IDFIELD) for i in range(start,min(len(hits),stop))]

    def _docIdForIdentifier(self, identifier):
        hits = self._searcher.search(TermQuery(Term(IDFIELD, identifier)))
        if len(hits) == 1:
            luceneId = hits.id(0)
            docId = self._tracker.map([luceneId]).next()
            return docId
        else:
            for command in self._documentQueue:
                if 'document' in command._kwargs:
                    docId = command._kwargs['document'].docId
                    return docId
        return None

    def getIndexReader(self):
        return self._reader

    def _delete(self, identifier):
        self._writer.deleteDocuments(Term(IDFIELD, identifier))

    def _add(self, document):
        document.addToIndexWith(self._writer)

    def delete(self, identifier):
        docId = self._docIdForIdentifier(identifier)
        if docId != None:
            self._tracker.deleteDocId(docId)
            self._documentQueue.append(FunctionCommand(self._delete, identifier=identifier))
            self.do.deleteDocument(docId=docId)
        return docId

    def addDocument(self, luceneDocument=None):
        docId = self._tracker.next()
        luceneDocument.docId = docId
        try:
            luceneDocument.validate()
            self._documentQueue.append(FunctionCommand(self._delete, identifier=luceneDocument.identifier))
            self._documentQueue.append(FunctionCommand(self._add, document=luceneDocument))
            self.do.addDocument(docId=docId, docDict=luceneDocument.asDict())
        except:
            self._documentQueue = []
            raise

    def commit(self):
        for item in self._documentQueue:
            item.execute()
        self._documentQueue = []
        self._reopenIndex()
        self._tracker.flush()

    def docCount(self):
        return self._reader.numDocs()

    def _getPyLuceneSort(self, sortBy, sortDescending):
        if sortBy and sortBy in self._existingFieldNames:
            return Sort(sortBy, bool(sortDescending))
        return None

    def close(self):
        self._writer and self._writer.close()
        self._reader = None
        self._searcher and self._searcher.close()

    def __del__(self):
        self.close()

    def start(self):
        self._reopenIndex()

    def isOptimized(self):
        return self.docCount() == 0 or self._reader.isOptimized()

    def getDirectory(self):
        return self._directoryName

    def getMergeFactor(self):
        return self._writer.getMergeFactor()

    def getMaxBufferedDocs(self):
        return self._writer.getMaxBufferedDocs()
