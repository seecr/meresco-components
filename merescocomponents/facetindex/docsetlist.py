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

from sys import maxint
from ctypes import c_uint32, c_char_p, POINTER, cdll, pointer, py_object, Structure, c_ulong, c_int, c_float, cast
from libfacetindex import libFacetIndex
from docset import DocSet, DOCSET
from integerlist import IntegerList
from cq2utils import deallocator

DOCSETLIST = POINTER(None)
CARDINALITYLIST = POINTER(None)

class cardinality_t(Structure):
    _fields_ = [('term',        c_char_p),
                ('cardinality', c_uint32)]

DocSetList_create = libFacetIndex.DocSetList_create
DocSetList_create.argtypes = []
DocSetList_create.restype = DOCSETLIST

DocSetList_delete = libFacetIndex.DocSetList_delete
DocSetList_delete.argtypes = [DOCSETLIST]
DocSetList_delete.restype = None

DocSetList_add = libFacetIndex.DocSetList_add
DocSetList_add.argtypes = [DOCSETLIST, DOCSET, c_char_p]
DocSetList_add.restype = None

DocSetList_removeDoc = libFacetIndex.DocSetList_removeDoc
DocSetList_removeDoc.argtypes = [DOCSETLIST, c_uint32]
DocSetList_removeDoc.restype = None

DocSetList_size = libFacetIndex.DocSetList_size
DocSetList_size.argtypes = [DOCSETLIST]
DocSetList_size.restype = int

def errcheck(result, func, arguments):
    if result.ptr == -1:
        raise IndexError('list index out of range')
    return result
DocSetList_get = libFacetIndex.DocSetList_get
DocSetList_get.argtypes = [DOCSETLIST, c_int]
DocSetList_get.restype = DOCSET
DocSetList_get.errcheck = errcheck

DocSetList_getForTerm = libFacetIndex.DocSetList_getForTerm
DocSetList_getForTerm.argtypes = [DOCSETLIST, c_char_p]
DocSetList_getForTerm.restype = DOCSET

DocSetList_combinedCardinalities = libFacetIndex.DocSetList_combinedCardinalities
DocSetList_combinedCardinalities.argtypes = [DOCSETLIST, DOCSET, c_uint32, c_int]
DocSetList_combinedCardinalities.restype = CARDINALITYLIST

DocSetList_getTermForDocset = libFacetIndex.DocSetList_getTermForDocset
DocSetList_getTermForDocset.argtypes = [DOCSETLIST, DOCSET]
DocSetList_getTermForDocset.restype = c_char_p

DocSetList_jaccards = libFacetIndex.DocSetList_jaccards
DocSetList_jaccards.argtypes = [DOCSETLIST, DOCSET, c_int, c_int, c_int, c_int]
DocSetList_jaccards.restype = CARDINALITYLIST
JACCARD_MI = c_int.in_dll(libFacetIndex, "JACCARD_MI")
JACCARD_X2 = c_int.in_dll(libFacetIndex, "JACCARD_X2")
JACCARD_ONLY = c_int.in_dll(libFacetIndex, "JACCARD_ONLY")

DocSetList_fromTermEnum = libFacetIndex.DocSetList_fromTermEnum
DocSetList_fromTermEnum.argtypes = [py_object, py_object, c_int]
DocSetList_fromTermEnum.restype = DOCSETLIST

DocSetList_sortOnCardinality = libFacetIndex.DocSetList_sortOnCardinality
DocSetList_sortOnCardinality.argtypes = [DOCSETLIST]
DocSetList_sortOnCardinality.restype = None

DocSetList_sortOnTerm = libFacetIndex.DocSetList_sortOnTerm
DocSetList_sortOnTerm.argtypes = [DOCSETLIST]
DocSetList_sortOnTerm.restype = None

DocSetList_printMemory = libFacetIndex.DocSetList_printMemory
DocSetList_printMemory.argtypes = [DOCSETLIST]
DocSetList_printMemory.restype = None

DocSetList_docId2terms_add = libFacetIndex.DocSetList_docId2terms_add
DocSetList_docId2terms_add.argtypes = [DOCSETLIST, c_uint32, DOCSET]
DocSetList_docId2terms_add.resType = None

CardinalityList_size = libFacetIndex.CardinalityList_size
CardinalityList_size.argtypes = [CARDINALITYLIST]
CardinalityList_size.restype = c_int

CardinalityList_at = libFacetIndex.CardinalityList_at
CardinalityList_at.argtypes = [CARDINALITYLIST, c_int]
CardinalityList_at.restype = POINTER(cardinality_t)

CardinalityList_free = libFacetIndex.CardinalityList_free
CardinalityList_free.argtypes = [CARDINALITYLIST]
CardinalityList_free.restype = None


SORTEDONTERM = 1
SORTEDONCARDINALITY = 2

class DocSetList(object):

    @classmethod
    def fromTermEnum(clazz, termEnum, termDocs, integerList=None):
        r = DocSetList_fromTermEnum(py_object(termEnum), py_object(termDocs), integerList.getCObject() if integerList else 0)
        return clazz(cobj=r)

    def __init__(self, cobj=None):
        if cobj:
            self._cobj = cobj
        else:
            self._cobj = DocSetList_create()
            self._dealloc = deallocator(DocSetList_delete, self._cobj)
        self._as_parameter_ = self._cobj
        self._sorted = None

    def __len__(self):
        return DocSetList_size(self)

    def __getitem__(self, i):
        """TESTING purposes"""
        item = DocSetList_get(self, i)
        return DocSet(cobj=item)

    def add(self, docset, term):
        if len(docset) == 0:
            return
        docset.releaseData()
        DocSetList_add(self, docset, term)
        self._sorted = None

    def termCardinalities(self, docset, maxResults=maxint, sorted=False):
        if sorted:
            self.sortOnCardinality()
        elif self._sorted == None:
            self.sortOnTerm()
        p = DocSetList_combinedCardinalities(self, docset, maxResults, sorted)
        try:
            for i in xrange(CardinalityList_size(p)):
                c = CardinalityList_at(p, i)
                yield (c.contents.term, c.contents.cardinality)
        finally:
            CardinalityList_free(p)

    def _TEST_getRawCardinalities(self, docset):
        class cardinality_t_RAW(Structure):
            _fields_ = [('term',        POINTER(None)),
                        ('cardinality', c_uint32)]
        cardinalityList_at_original_restype = CardinalityList_at.restype
        try:
            CardinalityList_at.restype = POINTER(cardinality_t_RAW)
            p = DocSetList_combinedCardinalities(self, docset, maxint, False)
            try:
                for i in xrange(CardinalityList_size(p)):
                    c = CardinalityList_at(p, i)
                    yield (c.contents.term, c.contents.cardinality)
            finally:
                CardinalityList_free(p)
        finally:
            CardinalityList_at.restype = cardinalityList_at_original_restype

    def allCardinalities(self):
        for docset in self:
            yield (DocSetList_getTermForDocset(self, docset), len(docset))

    def jaccards(self, docset, minimum, maximum, totaldocs, algorithm=JACCARD_MI):
        self.sortOnCardinality()
        p = DocSetList_jaccards(self, docset, minimum, maximum, totaldocs, algorithm)
        try:
            for i in xrange(CardinalityList_size(p)):
                c = CardinalityList_at(p, i)
                yield (c.contents.term, c.contents.cardinality)
        finally:
            CardinalityList_free(p)

    def addDocument(self, docid, terms):
        for term in (term.encode('utf-8') for term in terms):
            r = DocSetList_getForTerm(self, term)
            if r.ptr != -1:
                docset = DocSet(cobj=r)
                docset.add(docid)
                DocSetList_docId2terms_add(self, docid, docset)
                self._sorted = None
            else:
                docset = DocSet()
                docset.add(docid)
                self.add(docset, term)

    def deleteDoc(self, doc):
        DocSetList_removeDoc(self, doc)

    def sortOnCardinality(self):
        if self._sorted != SORTEDONCARDINALITY:
            DocSetList_sortOnCardinality(self)
            self._sorted = SORTEDONCARDINALITY

    def sortedOnCardinality(self):
        return self._sorted == SORTEDONCARDINALITY

    def sortOnTerm(self):
        if self._sorted != SORTEDONTERM:
            DocSetList_sortOnTerm(self)
            self._sorted = SORTEDONTERM

    def _TEST_getDocsetForTerm(self, term):
        r = DocSetList_getForTerm(self, term)
        if r:
            return DocSet(cobj=r)
        return None

    def termForDocset(self, docset):
        return DocSetList_getTermForDocset(self, docset)

    def applyDocIdMapping(self, mappingList):
        for docset in self:
            docset.applyDocIdMapping(mappingList)

    def printMemory(self):
        DocSetList_printMemory(self)
