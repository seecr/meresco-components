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

from os.path import isdir, isfile, join
from os import makedirs

from merescolucene import IndexReader, IndexWriter, IndexSearcher, Term, Field, TermQuery, Sort, merescoStandardAnalyzer, Query, iterJ
from java.lang import Object, String

from time import time
from itertools import ifilter, islice

from document import IDFIELD
from meresco.core import Observable

from docset import DocSet
from functioncommand import FunctionCommand
from lucenedocidtracker import LuceneDocIdTracker

IndexReader_FieldOption_ALL = IndexReader.FieldOption.ALL

class LuceneException(Exception):
    pass

class _Logger(object):
    def comment(self, *strings):
        self.writeLine('# ', *strings)
    def delete(self, identifier):
        self.writeLine('-', identifier)
    def add(self, identifier):
        self.writeLine('+', identifier)
    def commit(self):
        self.writeLine('=')

class DebugLogger(_Logger):
    def __init__(self, filename):
        self._file = open(filename, 'w')

    def writeLine(self, *strings):
        for aString in strings:
            self._file.write(str(aString))
        self._file.write('\n')

    def flush(self):
        self._file.flush()

class DevNullLogger(_Logger):
    def writeLine(self, *args):
        pass

class LuceneIndex(Observable):

    def __init__(self, directoryName, transactionName=None, debugLogFilename=None):
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
            merescoStandardAnalyzer,
            not IndexReader.indexExists(self._directoryName))
        self._reopenIndex()

        optimized = self.isOptimized()
        assert isfile(join(directoryName, 'tracker.segments')) or optimized, 'index must be optimized or tracker state must be present in directory'
        mergeFactor = self.getMergeFactor()
        maxBufferedDocs = self.getMaxBufferedDocs()
        assert mergeFactor == maxBufferedDocs, 'mergeFactor != maxBufferedDocs'
        maxDoc = self.docCount() if optimized else 0
        self._currentTracker = LuceneDocIdTracker(mergeFactor, directory=self._directoryName, maxDoc=maxDoc)
        self._lucene2docId = self._currentTracker.getMap()
        assert len(self._lucene2docId) == self._searcher.maxDoc(), "The docId tracker for the Lucene index in '%s' is out of sync (probably after a crash); Please optimize the index before restarting." % self._directoryName
        self._debugLog = DevNullLogger() if debugLogFilename == None else DebugLogger(debugLogFilename)
        self._debugLog.comment('Debug Log for LuceneIndex')
        self._debugLog.comment('directoryName = ', repr(directoryName))
        self._debugLog.comment('transactionName = ', transactionName)

    def getDocIdMapping(self):
        return self._lucene2docId

    def _reopenIndex(self):
        self._writer.flush()
        if self._reader:
            self._reader.close()
        self._reader = IndexReader.open(self._directoryName)
        if self._searcher:
            self._searcher.close()
        self._searcher = IndexSearcher(self._reader % IndexReader)
        self._existingFieldNames = self._reader.getFieldNames(IndexReader_FieldOption_ALL)

    def observer_init(self):
        self.do.indexStarted(self)

    def docsetFromQuery(self, pyLuceneQuery, **kwargs):
        return DocSet.fromQuery(self._searcher, pyLuceneQuery, self._lucene2docId)

    def executeQuery(self, pyLuceneQuery, start=0, stop=10, sortBy=None, sortDescending=None, docfilter=None, **kwargs):
        sortField = self._getPyLuceneSort(sortBy, sortDescending)
        if sortField:
            hits = self._searcher.search(pyLuceneQuery % Query, sortField)
        else:
            hits = self._searcher.search(pyLuceneQuery % Query)
        nrOfResults = hits.length()
        hits = iterJ(hits)
        if docfilter != None:
            hits = (hit for hit in hits if self._lucene2docId[hit.getId()] in docfilter)
            nrOfResults = len(docfilter)
        results = islice(hits, start, stop)
        class Response(object): pass
        response = Response()
        response.total = nrOfResults
        response.hits = [hit.getDocument().get(IDFIELD) for hit in results]
        raise StopIteration(response)
        yield

    def getIndexReader(self):
        return self._reader

    def _delete(self, identifier):
        self._writer.deleteDocuments(Term(IDFIELD, identifier))

    def _add(self, identifier, document):
        document.addToIndexWith(self._writer)

    def _docIdFromLastAddCommandFor(self, identifier):
        try:
            return (command for command in reversed(self._commandQueue) if command._kwargs['identifier'] == identifier and command.methodName() == '_add').next()._kwargs['document'].docId
        except StopIteration:
            return None

    def _luceneIdsForIdentifier(self, identifier):
        hits = self._searcher.search(TermQuery(Term(IDFIELD, identifier)) % Query)
        return (hit.getId() for hit in iterJ(hits))

    def _luceneDelete(self, identifier):
        docId = self._docIdFromLastAddCommandFor(identifier)
        if docId != None:
            docIds = [docId]
        else:
            docIds = (self._lucene2docId[luceneid] for luceneid in self._luceneIdsForIdentifier(identifier))
        for docId in docIds:
            deleted = self._currentTracker.deleteDocId(docId)
            if deleted:
                self._commandQueue.append(FunctionCommand(self._delete, identifier=identifier))
                self.do.deleteDocument(docId=docId)

    def delete(self, identifier):
        self._debugLog.delete(identifier)
        self._luceneDelete(identifier)

    def addDocument(self, luceneDocument=None):
        self._debugLog.add(luceneDocument.identifier)
        try:
            luceneDocument.validate()
            self._luceneDelete(luceneDocument.identifier)
            docId = self._currentTracker.next()
            luceneDocument.docId = docId
            self._commandQueue.append(FunctionCommand(self._add, identifier=luceneDocument.identifier, document=luceneDocument))
            self.do.addDocument(docId=docId, docDict=luceneDocument.asDict())
        except:
            self._commandQueue = []
            raise

    def begin(self):
        if self.ctx.tx.name == self._transactionName:
            self.ctx.tx.join(self)

    def commit(self):
        self._debugLog.commit()
        if len(self._commandQueue) == 0:
            return
        for command in self._commandQueue:
            command.execute()
        self._commandQueue = []
        self._reopenIndex()
        self._currentTracker.flush()
        self._lucene2docId = self._currentTracker.getMap()

    def rollback(self):
        pass

    def docCount(self):
        return self._reader.numDocs()

    def _getPyLuceneSort(self, sortBy, sortDescending):
        if sortBy and self._existingFieldNames.contains(String(sortBy) % Object):
            return Sort(sortBy, bool(sortDescending))
        return None

    def listFields(self):
        return iterJ(self._existingFieldNames)

    def close(self):
        self._writer and self._writer.close()
        self._reader = None
        self._searcher and self._searcher.close()

    def __del__(self):
        self.close()

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
