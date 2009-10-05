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
from os.path import dirname, abspath, join
from ctypes import cdll, c_int, c_uint32, POINTER, py_object, c_char_p, Structure
from libfacetindex import libFacetIndex
from integerlist import INTEGERLIST
from cq2utils import deallocator

class DOCSET(Structure):
    _fields_ = [("type", c_int, 2),
                ("ptr", c_int, 30)]

    def isNone(self):
        return self.type == 0 and self.ptr == -1

DocSet_create = libFacetIndex.DocSet_create
DocSet_create.argtypes = [c_int]
DocSet_create.restype = DOCSET

DocSet_contains = libFacetIndex.DocSet_contains
DocSet_contains.argtypes = [DOCSET, c_uint32]
DocSet_contains.restype = c_int

DocSet_add = libFacetIndex.DocSet_add
DocSet_add.argtypes = [DOCSET, c_uint32]
DocSet_add.restype = None

DocSet_merge = libFacetIndex.DocSet_merge
DocSet_merge.argtypes = [DOCSET, DOCSET]
DocSet_merge.restype = None

DocSet_remove = libFacetIndex.DocSet_remove
DocSet_remove.argtypes = [DOCSET, c_uint32]
DocSet_remove.restype = None

DocSet_get = libFacetIndex.DocSet_get
DocSet_get.argtypes = [DOCSET, c_int]
DocSet_get.restype = c_uint32

DocSet_len = libFacetIndex.DocSet_len
DocSet_len.argtypes = [DOCSET]
DocSet_len.restype = int

DocSet_combinedCardinality = libFacetIndex.DocSet_combinedCardinality
DocSet_combinedCardinality.argtypes = [DOCSET, DOCSET]
DocSet_combinedCardinality.restype = c_int

DocSet_combinedCardinalitySearch = libFacetIndex.DocSet_combinedCardinalitySearch
DocSet_combinedCardinalitySearch.argtype = [DOCSET, DOCSET]
DocSet_combinedCardinalitySearch.restype = c_int

DocSet_intersect = libFacetIndex.DocSet_intersect
DocSet_intersect.argtypes = [DOCSET, DOCSET]
DocSet_intersect.restype = DOCSET

DocSet_fromQuery = libFacetIndex.DocSet_fromQuery
DocSet_fromQuery.argtypes = [py_object, py_object, POINTER(None)]
DocSet_fromQuery.restype = DOCSET

DocSet_fromTermDocs = libFacetIndex.DocSet_fromTermDocs
DocSet_fromTermDocs.argtypes = [py_object, c_int, POINTER(None)]
DocSet_fromTermDocs.restype = DOCSET

DocSet_forTesting = libFacetIndex.DocSet_forTesting
DocSet_forTesting.argtypes = [c_int]
DocSet_forTesting.restype = DOCSET

DocSet_delete = libFacetIndex.DocSet_delete
DocSet_delete.argtypes = [DOCSET]
DocSet_delete.restype = None


class DocSet(object):

    @classmethod
    def fromQuery(clazz, searcher, query, mapping=None):
        r = DocSet_fromQuery(py_object(searcher), py_object(query), mapping)
        if r.isNone():
            raise Exception("org.apache.lucene.search.BooleanQuery$TooManyClauses")
        return clazz(cobj=r, own=True)

    @classmethod
    def fromTermDocs(clazz, termdocs, freq, mapping=None):
        r = DocSet_fromTermDocs(py_object(termdocs), freq, mapping)
        return clazz(cobj=r, own=True)

    @classmethod
    def forTesting(clazz, size):
        r = DocSet_forTesting(size)
        c = clazz(cobj=r, own=True)
        return c

    def __init__(self, data=[], cobj=None, own=False):
        if cobj:
            self._cobj = cobj
            self._own_cobj = deallocator(DocSet_delete, self._cobj) if own else False
        else:
            self._cobj = DocSet_create(0)
            self._own_cobj = deallocator(DocSet_delete, self._cobj)
        self._as_parameter_ = self._cobj
        for i in data:
            DocSet_add(self._cobj, i)

    def __len__(self):
        return DocSet_len(self)

    def __iter__(self):
        for i in xrange(len(self)):
            yield DocSet_get(self, i)

    def __contains__(self, value):
        return DocSet_contains(self, value)

    def __eq__(self, rhs):
        return list(iter(self)) == list(iter(rhs))

    def __repr__(self):
        return repr(list(iter(self)))

    def __getitem__(self, i):
        return DocSet_get(self, i)

    def add(self, doc):
        l = DocSet_len(self)
        lastDoc = DocSet_get(self, l-1)
        if l > 0 and doc <= lastDoc:
            raise Exception('non-increasing docid: %d must be > %d, (length %d)' % (doc, lastDoc, l))
        DocSet_add(self._cobj, doc)

    def merge(self, anotherDocSet):
        DocSet_merge(self, anotherDocSet)

    def delete(self, doc):
        DocSet_remove(self, doc)

    def releaseData(self):
        assert self._own_cobj, 'object already released, perhaps duplicate add()?'
        self._own_cobj.next()
        self._own_cobj = False;

    def combinedCardinality(self, rhs):
        return DocSet_combinedCardinality(self, rhs)

    def intersect(self, rhs):
        r = DocSet_intersect(self, rhs)
        return DocSet(cobj=r, own=True)
