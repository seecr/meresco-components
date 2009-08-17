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
from .docsetlist import DocSetList, JACCARD_MI
from PyLucene import Term, IndexReader # hmm, maybe we don't want this dependency?
from time import time
from sys import maxint
from functioncommand import FunctionCommand
from callstackscope import callstackscope
from .triedict import TrieDict
from collections import defaultdict

class NoFacetIndexException(Exception):

    def __init__(self, field, fields):
        self._str = "No facetindex for field '%s'. Available fields: %s" % (field, ', '.join("'%s'" % field for field in fields))

    def __str__(self):
        return self._str


class Drilldown(object):

    def __init__(self, staticDrilldownFieldnames=None, transactionName=None):
        self._staticDrilldownFieldnames = staticDrilldownFieldnames
        self._actualDrilldownFieldnames = self._staticDrilldownFieldnames
        self._docsetlists = {}
        if self._staticDrilldownFieldnames:
            self._docsetlists = dict((fieldname, DocSetList()) for fieldname in self._staticDrilldownFieldnames)
        self._commandQueue = []
        self._transactionName = transactionName

    def _add(self, docId, docDict):
        keys = docDict.keys()
        fieldnames = (fieldname
            for fieldname in keys
                if fieldname in self._actualDrilldownFieldnames)
        for fieldname in fieldnames:
            self._docsetlists[fieldname].addDocument(docId, docDict[fieldname])

        compoundFields = (field for field in self._actualDrilldownFieldnames if type(field) == tuple)
        values = defaultdict(set)
        for field in compoundFields:
            for fieldname in field:
                if fieldname in keys:
                    for i in docDict[fieldname]:
                        values[field].add(i)
        for field, value in values.items():
            self._docsetlists[field].addDocument(docId, value)

    def addDocument(self, docId, docDict):
        self.deleteDocument(docId)
        self._commandQueue.append(FunctionCommand(self._add, docId=docId, docDict=docDict))

    def _delete(self, docId):
        for docsetlist in self._docsetlists.values():
            docsetlist.deleteDoc(docId)

    def commit(self):
        #print "Drilldown->commit()", len(self._commandQueue), str(self._commandQueue)
        try:
            for command in self._commandQueue:
                command.execute()
        finally:
            self._commandQueue = []

    def rollback(self):
        pass

    def begin(self):
        tx = callstackscope('__callstack_var_tx__') # rather derive from Observable oid and use self.tx
        if tx.name == self._transactionName:
            tx.join(self)

    def deleteDocument(self, docId):
        self._commandQueue.append(FunctionCommand(self._delete, docId=docId))

    def indexStarted(self, indexReader, docIdMapping=None):
        t0 = time()

        self._totaldocs = indexReader.numDocs()
        fieldNames = self._staticDrilldownFieldnames
        if not fieldNames:
            fieldNames = [fieldname
                for fieldname in indexReader.getFieldNames(IndexReader.FieldOption.ALL)
                    if not fieldname.startswith('__')]
        for fieldname in fieldNames:
            if type(fieldname) == tuple:
                self._docsetlists[fieldname] = DocSetList()
                for field in fieldname:
                    self._docsetlists[fieldname].merge(self._docSetListFromTermEnumForField(field, indexReader, docIdMapping))
            else:
                self._docsetlists[fieldname] = self._docSetListFromTermEnumForField(fieldname, indexReader, docIdMapping)

        self._actualDrilldownFieldnames = fieldNames
        #print 'indexStarted (ms)', (time()-t0)*1000
        #print self.measure()

    def _docSetListFromTermEnumForField(self, field, indexReader, docIdMapping):
        termDocs = indexReader.termDocs()
        termEnum = indexReader.terms(Term(field, ''))
        return DocSetList.fromTermEnum(termEnum, termDocs, docIdMapping)

    def drilldown(self, docset, drilldownFieldnamesAndMaximumResults=None):
        if not drilldownFieldnamesAndMaximumResults:
            drilldownFieldnamesAndMaximumResults = [(fieldname, 0, False)
                for fieldname in self._actualDrilldownFieldnames]
        for fieldname, maximumResults, sorted in drilldownFieldnamesAndMaximumResults:
            if fieldname not in self._actualDrilldownFieldnames:
                raise NoFacetIndexException(fieldname, self._actualDrilldownFieldnames)
            yield fieldname, self._docsetlists[fieldname].termCardinalities(docset, maximumResults or maxint, sorted)

    def jaccard(self, docset, jaccardFieldsAndRanges, algorithm=JACCARD_MI, maxTermFreqPercentage=100):
        for fieldname, minimum, maximum in jaccardFieldsAndRanges:
            if fieldname not in self._docsetlists:
                raise NoFacetIndexException(fieldname, self._actualDrilldownFieldnames)
            yield fieldname, self._docsetlists[fieldname].jaccards(docset, minimum, maximum,
                    self._totaldocs, algorithm=algorithm, maxTermFreqPercentage=maxTermFreqPercentage)

    def queueLength(self):
        return len(self._commandQueue)

    def intersect(self, fieldname, docset):
        return self._docsetlists[fieldname].intersect(docset)

    def measure(self):
        totalBytes = 0
        terms = 0
        postings = 0
        for docsetlist in self._docsetlists.values():
            totalBytes += docsetlist.measure()
            terms += len(docsetlist)
            postings += sum(len(docset) for docset in docsetlist)
        dictionaries = TrieDict.measureall()
        return {'dictionaries':dictionaries, 'postings': postings, 'terms': terms, 'fields': len(self._docsetlists), 'totalBytes': totalBytes}