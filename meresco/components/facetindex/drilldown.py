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
#    Copyright (C) 2011 Maastricht University http://www.um.nl
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

from docset import DocSet
from docsetlist import DocSetList, JACCARD_MI
from merescolucene import Term, IndexReader, iterJ  
from time import time
from sys import maxint
from functioncommand import FunctionCommand
from .triedict import TrieDict
from collections import defaultdict
from weightless.core import local

IndexReader_FieldOption_ALL = IndexReader.FieldOption.ALL


class NoFacetIndexException(Exception):
    def __init__(self, field, fields):
        Exception.__init__(self, "No facetindex for field '%s'. Available fields: %s" % (field, ', '.join("'%s'" % field for field in fields)))
        self.field = field
        self.fields = fields

class Drilldown(object):

    def __init__(self, drilldownFields=None, transactionName=None):
        self._drilldownFields = []
        self._prefixes = []
        self._compoundFields = []
        for field in drilldownFields if drilldownFields else []:
            if type(field) == tuple:
                self._compoundFields.append(field)
            elif field.endswith('*'):
                self._prefixes.append(field.rstrip('*'))
            else:
                self._drilldownFields.append(field)
        self._docsetlists = defaultdict(DocSetList)
        self._commandQueue = []
        self._transactionName = transactionName

    def _add(self, docId, docDict):
        for field in docDict.keys():
            if self._isDrilldownField(field):
                self._docsetlists[field].addDocument(docId, docDict[field])

        for compoundField in self._compoundFields:
            terms = set(term for field in compoundField \
                            for term in docDict.get(field, []))
            self._docsetlists[compoundField].addDocument(docId, terms)

    def _isDrilldownField(self, field):
        if type(field) == tuple and field in self._compoundFields:
            return True
        if field.startswith('__'):
            return False
        if field in self._drilldownFields:
            return True
        for prefix in self._prefixes:
            if field.startswith(prefix):
                return True
        return False

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
        tx = local('__callstack_var_tx__')
        if tx.name == self._transactionName:
            tx.join(self)

    def deleteDocument(self, docId):
        self._commandQueue.append(FunctionCommand(self._delete, docId=docId))

    def indexStarted(self, index):
        t0 = time()
        indexReader = index.getIndexReader()
        docIdMapping = index.getDocIdMapping()
        self._index = index
        for field in self._determineDrilldownFields(indexReader):
            self._docsetlists[field] = self._docSetListFromTermEnumForField(field, indexReader, docIdMapping)
        for compoundField in self._compoundFields:
            for field in compoundField:
                docsetlist = self._docsetlists[field] if field in self._docsetlists else self._docSetListFromTermEnumForField(field, indexReader, docIdMapping)
                self._docsetlists[compoundField].merge(docsetlist)

        #print 'indexStarted (ms)', (time()-t0)*1000
        #print self.measure()

    def _determineDrilldownFields(self, indexReader):
        result = set(self._drilldownFields)
        result.update(fieldname for fieldname in \
            iterJ(indexReader.getFieldNames(IndexReader_FieldOption_ALL)) \
                if self._isDrilldownField(fieldname))
        return result

    def _docSetListFromTermEnumForField(self, field, indexReader, docIdMapping):
        return DocSetList.forField(indexReader, field, docIdMapping)

    def docsetlist(self, field):
        return self._docsetlists[field]

    def listFields(self):
        return self._docsetlists.keys()

    def drilldown(self, docset, drilldownFieldnamesAndMaximumResults=None, defaultMaximumResults=0, defaultSorting=False):
        if not drilldownFieldnamesAndMaximumResults:
            drilldownFieldnamesAndMaximumResults = [
                (fieldname, defaultMaximumResults, defaultSorting)
                for fieldname in self._docsetlists]
        for fieldname, maximumResults, howToSort in drilldownFieldnamesAndMaximumResults:
            if not self._isDrilldownField(fieldname):
                raise NoFacetIndexException(fieldname, self.listFields())

            docsetlist = self._docsetlists[fieldname]
            yield fieldname, docsetlist.termCardinalities(docset, maximumResults or maxint, howToSort)

    def hierarchicalDrilldown(self, docset, drilldownFieldnamesAndMaximumResults=None, defaultMaximumResults=0, defaultSorting=False):
        if not drilldownFieldnamesAndMaximumResults:
            drilldownFieldnamesAndMaximumResults = [
                (fieldname, defaultMaximumResults, defaultSorting)
                for fieldname in self._docsetlists]
        for fieldname, maximumResults, howToSort in drilldownFieldnamesAndMaximumResults:
            if fieldname == []:
                raise StopIteration()
            fieldname, remainingFields = fieldname[0], fieldname[1:]

            if not self._isDrilldownField(fieldname):
                raise NoFacetIndexException(fieldname, self.listFields())

            docsetlist = self._docsetlists[fieldname]
            termCardinalities = docsetlist.termCardinalities(docset, maximumResults or maxint, howToSort)
            yield dict(fieldname=fieldname, terms=self._buildHierarchicalDrilldownTree(
                        docset, docsetlist, termCardinalities, 
                        [(remainingFields, maximumResults, howToSort)]))

    def _buildHierarchicalDrilldownTree(self, docset, docsetlist, termCardinalities, drilldownFieldnamesAndMaximumResults):
        #intersectedDocsetlist = docsetlist.intersect(docset)
        for term, cardinality in termCardinalities:
            docsetForTerm = docsetlist._TEST_getDocsetForTerm(term)
            intersectedTermDocset = DocSet(sorted(docsetForTerm.intersect(docset)))
            yield dict(term=term, count=cardinality, remainder=self.hierarchicalDrilldown(intersectedTermDocset, drilldownFieldnamesAndMaximumResults))

    def jaccard(self, docset, jaccardFieldsAndRanges, algorithm=JACCARD_MI, maxTermFreqPercentage=100):
        for fieldname, minimum, maximum in jaccardFieldsAndRanges:
            if fieldname not in self._docsetlists:
                raise NoFacetIndexException(fieldname, self._docsetlists.keys())
            yield fieldname, self._docsetlists[fieldname].jaccards(docset, minimum, maximum,
                    self._index.docCount(), algorithm=algorithm, maxTermFreqPercentage=maxTermFreqPercentage)

    def queueLength(self):
        return len(self._commandQueue)

    def intersect(self, fieldname, docset):
        return self._docsetlists[fieldname].intersect(docset)

    def prefixSearch(self, fieldname, prefix, maxresults=None):
        return self._docsetlists[fieldname].prefixSearch(prefix=prefix, maxresults=maxresults)

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
