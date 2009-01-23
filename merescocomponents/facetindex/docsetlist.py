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

from sys import maxint
from ctypes import c_uint32, c_char_p, POINTER, cdll, pointer, py_object, Structure, c_ulong, c_int, c_float, cast
from docset import DocSet, libDocSet

SELF = POINTER(None)

def errcheck(result, func, arguments):
    if not result:
        raise IndexError('list index out of range')
    return result

class cardinality_t(Structure):
    _fields_ = [('term',        c_char_p),
                ('cardinality', c_uint32)]

DocSetList_create = libDocSet.DocSetList_create
DocSetList_create.argtypes = []
DocSetList_create.restype = SELF

DocSetList_delete = libDocSet.DocSetList_delete
DocSetList_delete.argtypes = [SELF]
DocSetList_delete.restype = None

DocSetList_add = libDocSet.DocSetList_add
DocSetList_add.argtypes = [SELF, SELF]
DocSetList_add.restype = None

DocSetList_removeDoc = libDocSet.DocSetList_removeDoc
DocSetList_removeDoc.argtypes = [SELF, c_uint32]
DocSetList_removeDoc.restype = None

DocSetList_size = libDocSet.DocSetList_size
DocSetList_size.argtypes = [SELF]
DocSetList_size.restype = int

DocSetList_get = libDocSet.DocSetList_get
DocSetList_get.argtypes = [SELF, c_int]
DocSetList_get.restype = SELF
DocSetList_get.errcheck = errcheck

DocSetList_getForTerm = libDocSet.DocSetList_getForTerm
DocSetList_getForTerm.argtypes = [SELF, c_char_p]
DocSetList_getForTerm.restype = POINTER(None)

DocSetList_combinedCardinalities = libDocSet.DocSetList_combinedCardinalities
DocSetList_combinedCardinalities.argtypes = [SELF, SELF, c_uint32, c_int]
DocSetList_combinedCardinalities.restype = SELF # *CardinalityList

DocSetList_jaccards = libDocSet.DocSetList_jaccards
DocSetList_jaccards.argtypes = [SELF, SELF, c_int, c_int, c_int, c_int]
DocSetList_jaccards.restype = SELF  # *CardinalityList
JACCARD_MI = c_int.in_dll(libDocSet, "JACCARD_MI")
JACCARD_X2 = c_int.in_dll(libDocSet, "JACCARD_X2")
JACCARD_ONLY = c_int.in_dll(libDocSet, "JACCARD_ONLY")

DocSetList_fromTermEnum = libDocSet.DocSetList_fromTermEnum
DocSetList_fromTermEnum.argtypes = [py_object, py_object]
DocSetList_fromTermEnum.restype = SELF

DocSetList_sortOnCardinality = libDocSet.DocSetList_sortOnCardinality
DocSetList_sortOnCardinality.argtypes = [SELF]
DocSetList_sortOnCardinality.restype = None

CardinalityList_size = libDocSet.CardinalityList_size
CardinalityList_size.argtypes = [SELF]
CardinalityList_size.restype = c_int

CardinalityList_at = libDocSet.CardinalityList_at
CardinalityList_at.argtypes = [SELF, c_int]
CardinalityList_at.restype = POINTER(cardinality_t)

CardinalityList_free = libDocSet.CardinalityList_free
CardinalityList_free.argtypes = [SELF]
CardinalityList_free.restype = None

class DocSetList(object):

    @classmethod
    def fromTermEnum(clazz, termEnum, termDocs):
        r = DocSetList_fromTermEnum(py_object(termEnum), py_object(termDocs))
        return clazz(r)

    def __init__(self, cobj=None):
        if cobj:
            self._cobj = cobj
        else:
            self._cobj = DocSetList_create()
        self._as_parameter_ = self._cobj
        self._sorted = False

    def __del__(self):
        DocSetList_delete(self)

    def __len__(self):
        return DocSetList_size(self)

    def __getitem__(self, i):
        item = DocSetList_get(self, i)
        return DocSet(cobj=item)

    def add(self, docset):
        if len(docset) == 0:
            return
        docset.releaseData()
        DocSetList_add(self, docset)
        self._sorted = False

    def termCardinalities(self, docset, maxResults=maxint, sorted=False):
        if sorted:
            self.sortOnCardinality()
        p = DocSetList_combinedCardinalities(self, docset, maxResults, sorted)
        try:
            for i in xrange(CardinalityList_size(p)):
                c = CardinalityList_at(p, i)
                yield (c.contents.term, c.contents.cardinality)
        finally:
            CardinalityList_free(p)

    def allCardinalities(self):
        for docset in self:
            yield (docset.term(), len(docset))

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
        for term in terms:
            r = DocSetList_getForTerm(self, term)
            if r:
                docset = DocSet(cobj=r)
                docset.add(docid)
                self._sorted = False
            else:
                docset = DocSet(term)
                docset.add(docid)
                self.add(docset)

    def deleteDoc(self, doc):
        DocSetList_removeDoc(self, doc)

    def sortOnCardinality(self):
        if not self._sorted:
            DocSetList_sortOnCardinality(self)
            self._sorted = True

    def sorted(self):
        return self._sorted
