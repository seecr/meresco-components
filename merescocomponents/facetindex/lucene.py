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

from os.path import isdir, isfile, join
from os import makedirs
from PyLucene import IndexReader, IndexWriter, IndexSearcher, StandardAnalyzer, Term, Field, TermQuery, Sort,  StandardTokenizer, StandardFilter, LowerCaseFilter, QueryFilter
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

    def __init__(self, directoryName, transactionName=None):
        Observable.__init__(self)
        self._searcher = None
        self._reader = None
        self._writer = None
        self._transactionName = transactionName
        self._commandQueue = []
        self._directoryName = directoryName
        if not isdir(self._directoryName):
            makedirs(self._directoryName)

        self._writer = IndexWriter(
            self._directoryName,
            IncludeStopWordAnalyzer(), not IndexReader.indexExists(self._directoryName))
        self._reopenIndex()

        optimized = self.isOptimized()
        assert isfile(join(directoryName, 'tracker.segments')) or optimized, 'index must be optimized or tracker state must be present in directory'
        mergeFactor = self.getMergeFactor()
        maxBufferedDocs = self.getMaxBufferedDocs()
        assert mergeFactor == maxBufferedDocs, 'mergeFactor != maxBufferedDocs'
        maxDoc = self.docCount() if optimized else 0
        self._tracker = LuceneDocIdTracker(mergeFactor, directory=self._directoryName, maxDoc=maxDoc)
        self._lucene2docId = self._tracker.getMap()

    def getDocIdMapping(self):
        return self._lucene2docId

    def _reopenIndex(self):
        self._writer.flush()
        if self._reader:
            self._reader.close()
        self._reader = IndexReader.open(self._directoryName)
        if self._searcher:
            self._searcher.close()
        self._searcher = IndexSearcher(self._reader)
        self._existingFieldNames = self._reader.getFieldNames(IndexReader.FieldOption.ALL)

    def observer_init(self):
        self.do.indexStarted(self._reader, docIdMapping=self._lucene2docId)

    def docsetFromQuery(self, pyLuceneQuery):
        return DocSet.fromQuery(self._searcher, pyLuceneQuery, self._lucene2docId)

    def _filterHits(self, hits, start, stop, filter):
        results = 0
        for i in range(len(hits)):
            if self._lucene2docId[hits.id(i)] in filter:
                results += 1
                if results > stop:
                    return
                if results > start :
                    yield hits[i].get(IDFIELD)


    def executeQuery(self, pyLuceneQuery, start=0, stop=10, sortBy=None, sortDescending=None, filter=None):
        sortField = self._getPyLuceneSort(sortBy, sortDescending)
        if sortField:
            hits = self._searcher.search(pyLuceneQuery, sortField)
        else:
            hits = self._searcher.search(pyLuceneQuery)
        if filter == None:
            return len(hits), [hits[i].get(IDFIELD) for i in range(start,min(len(hits),stop))]
        result = list(self._filterHits(hits, start, stop, filter))
        return len(result), result


    def _luceneIdForIdentifier(self, identifier):
        hits = self._searcher.search(TermQuery(Term(IDFIELD, identifier)))
        if len(hits) == 1:
            return hits.id(0)
        return None

    def getIndexReader(self):
        return self._reader

    def _delete(self, identifier):
        self._writer.deleteDocuments(Term(IDFIELD, identifier))

    def _add(self, document):
        document.addToIndexWith(self._writer)

    def _luceneDelete(self, identifier):
        docId = None
        luceneId = self._luceneIdForIdentifier(identifier)
        if luceneId == None:  # not in index, perhaps it is in the queue?
            for command in self._commandQueue:
                if 'document' in command._kwargs:
                    if command._kwargs['document'].identifier == identifier:
                        docId = command._kwargs['document'].docId
                        break
        else:  # in index, so delete it first
            # it might already have been delete by a previous delete()
            if not self._tracker.isDeleted(luceneId):
                docId = self._tracker.map([luceneId]).next()
                self._tracker.deleteLuceneId(luceneId)
        if docId != None:
            self._commandQueue.append(FunctionCommand(self._delete, identifier=identifier))
        return docId

    def delete(self, identifier):
        docId = self._luceneDelete(identifier)
        if docId != None:
            self.do.deleteDocument(docId=docId)

    def addDocument(self, luceneDocument=None):
        try:
            luceneDocument.validate()
            self._luceneDelete(luceneDocument.identifier)
            docId = self._tracker.next()
            luceneDocument.docId = docId
            #luceneDocument._document.add(Field('docId', str(docId), Field.Store.YES, Field.Index.UN_TOKENIZED))
            self._commandQueue.append(FunctionCommand(self._add, document=luceneDocument))
            self.do.addDocument(docId=docId, docDict=luceneDocument.asDict())
        except:
            self._commandQueue = []
            raise

    def begin(self):
        if self.tx.name == self._transactionName:
            self.tx.join(self)

    def commit(self):
        for command in self._commandQueue:
            command.execute()
        self._commandQueue = []
        self._reopenIndex()
        self._tracker.flush()
        self._lucene2docId = self._tracker.getMap()

    def rollback(self):
        pass

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
        self.do.indexStarted(self._reader)

    def isOptimized(self):
        return self.docCount() == 0 or self._reader.isOptimized()

    def getDirectory(self):
        return self._directoryName

    def getMergeFactor(self):
        return self._writer.getMergeFactor()

    def getMaxBufferedDocs(self):
        return self._writer.getMaxBufferedDocs()

    def queueLength(self):
        return len(self._commandQueue)
