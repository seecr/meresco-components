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
from .docsetlist import DocSetList
from PyLucene import Term, IndexReader # hmm, maybe we don't want this dependency?
from time import time
from sys import maxint

class NoFacetIndexException(Exception):

    def __init__(self, field, fields):
        self._str = "No facetindex for field '%s'. Available fields: %s" % (field, ', '.join("'%s'" % field for field in fields))

    def __str__(self):
        return self._str


class Drilldown(object):

    def __init__(self, staticDrilldownFieldnames=None):
        self._staticDrilldownFieldnames = staticDrilldownFieldnames
        self._actualDrilldownFieldnames = self._staticDrilldownFieldnames
        self._docsetlists = {}

    def addDocument(self, docId, fieldAndTermsList):
        for fieldname, terms in fieldAndTermsList:
            if fieldname in self._actualDrilldownFieldnames:
                self._fieldMatrices[fieldname].addDocument(docId, terms)

    def deleteDocument(self, docId):
        for fieldname in self._actualDrilldownFieldnames:
            self._fieldMatrices[fieldname].deleteDocument(docId)

    def indexStarted(self, indexReader):
        t0 = time()
        self._totaldocs = indexReader.numDocs()
        termDocs = indexReader.termDocs()
        fieldNames = self._staticDrilldownFieldnames
        if not fieldNames:
            fieldNames = [fieldname
                for fieldname in indexReader.getFieldNames(IndexReader.FieldOption.ALL)
                    if not fieldname.startswith('__')]
        for fieldname in fieldNames:
            termEnum = indexReader.terms(Term(fieldname,''))
            self._docsetlists[fieldname] = DocSetList.fromTermEnum(termEnum, termDocs)
        self._actualDrilldownFieldnames = fieldNames
        print 'indexStarted (ms)', (time()-t0)*1000

    def drilldown(self, docset, drilldownFieldnamesAndMaximumResults=[]):
        if not drilldownFieldnamesAndMaximumResults:
            drilldownFieldnamesAndMaximumResults = [(fieldname, 0, False)
                for fieldname in self._actualDrilldownFieldnames]
        for fieldname, maximumResults, sorted in drilldownFieldnamesAndMaximumResults:
            if fieldname not in self._actualDrilldownFieldnames:
                raise NoFacetIndexException(fieldname, self._actualDrilldownFieldnames)
            t0 = time()
            try:
                yield fieldname, self._docsetlists[fieldname].termCardinalities(docset, maximumResults or maxint, sorted)
            finally:
                print 'drilldown (ms)', fieldname, (time()-t0)*1000

    def jaccard(self, docset, jaccardFieldsAndRanges):
        for fieldname, minimum, maximum in jaccardFieldsAndRanges:
            if fieldname not in self._docsetlists:
                raise NoFacetIndexException(fieldname, self._actualDrilldownFieldnames)
            yield fieldname, self._docsetlists[fieldname].jaccards(docset, minimum, maximum, self._totaldocs)


    def rowCardinalities(self):
        for fieldname in self._actualDrilldownFieldnames:
            yield fieldname, self._fieldMatrices[fieldname].allRowCardinalities()

    def prefixDrilldown(self, fieldname, prefix, row, maximumResults=0):
        return self._fieldMatrices[fieldname].prefixDrilldown(prefix, row, maximumResults)

