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
from os.path import dirname, abspath, join
from ctypes import cdll, c_int, c_uint32, POINTER, py_object, c_char_p

SELF = POINTER(None)

docsetpointer = POINTER(c_uint32)
def docsettype(size):
    return (c_uint32*size)

import PyLucene # make sure PyLucene/Java is initialized before loading _docset.so
libDocSet = cdll.LoadLibrary(join(abspath(dirname(__file__)), '_facetindex.so'))

DocSet_create = libDocSet.DocSet_create
DocSet_create.argtypes = []
DocSet_create.restype = SELF

DocSet_add = libDocSet.DocSet_add
DocSet_add.argtypes = [SELF, c_uint32]
DocSet_add.restype = None

DocSet_remove = libDocSet.DocSet_remove
DocSet_remove.argtypes = [SELF, c_uint32]
DocSet_remove.restype = None

DocSet_get = libDocSet.DocSet_get
DocSet_get.argtypes = [SELF, c_int]
DocSet_get.restype = c_uint32

DocSet_len = libDocSet.DocSet_len
DocSet_len.argtypes = [SELF]
DocSet_len.restype = int

DocSet_term = libDocSet.DocSet_term
DocSet_term.argtypes = [SELF]
DocSet_term.restype = c_char_p

DocSet_setTerm = libDocSet.DocSet_setTerm
DocSet_setTerm.argtypes = [SELF, c_char_p]
DocSet_setTerm.restype = None

DocSet_combinedCardinality = libDocSet.DocSet_combinedCardinality
DocSet_combinedCardinality.argtypes = [SELF, SELF]
DocSet_combinedCardinality.restype = c_int

DocSet_combinedCardinalitySearch = libDocSet.DocSet_combinedCardinalitySearch
DocSet_combinedCardinalitySearch.argtype = [SELF, SELF]
DocSet_combinedCardinalitySearch.restype = c_int

DocSet_intersect = libDocSet.DocSet_intersect
DocSet_intersect.argtypes = [SELF, SELF]
DocSet_intersect.restype = SELF

DocSet_fromQuery = libDocSet.DocSet_fromQuery
DocSet_fromQuery.argtypes = [py_object, py_object, SELF]
DocSet_fromQuery.restype = SELF

DocSet_fromTermDocs = libDocSet.DocSet_fromTermDocs
DocSet_fromTermDocs.argtypes = [py_object, c_int, c_char_p, SELF]
DocSet_fromTermDocs.restype = SELF

DocSet_forTesting = libDocSet.DocSet_forTesting
DocSet_forTesting.argtypes = [c_int]
DocSet_forTesting.restype = SELF

DocSet_delete = libDocSet.DocSet_delete
DocSet_delete.argtypes = [SELF]
DocSet_delete.restype = None

class DocSet(object):

    @classmethod
    def fromQuery(clazz, searcher, query, mapping=None):
        r = DocSet_fromQuery(py_object(searcher), py_object(query), mapping)
        return clazz(cobj=r)

    @classmethod
    def fromTermDocs(clazz, termdocs, freq, term="", mapping=None):
        r = DocSet_fromTermDocs(py_object(termdocs), freq, term, mapping)
        return clazz(cobj=r)

    @classmethod
    def forTesting(clazz, size):
        r = DocSet_forTesting(size)
        c = clazz(cobj=r, term='test')
        c._own_cobj = True;
        return c

    def __init__(self, term='', data=[], cobj=None, ):
        if cobj:
            self._cobj = cobj
            self._own_cobj = False
        else:
            self._cobj = DocSet_create()
            self._own_cobj = True
            for i in data:
                DocSet_add(self._cobj, i)
        self._as_parameter_ = self._cobj
        if term:
            DocSet_setTerm(self, term)

    def __del__(self):
        if self._own_cobj:
            DocSet_delete(self)

    def __len__(self):
        return DocSet_len(self)

    def __iter__(self):
        for i in xrange(len(self)):
            yield DocSet_get(self, i)

    def __eq__(self, rhs):
        return list(iter(self)) == list(iter(rhs))

    def __repr__(self):
        return repr(list(iter(self)))

    def __getitem__(self, i):
        return DocSet_get(self, i)

    def add(self, doc):
        l = DocSet_len(self)
        if l > 0 and doc <= DocSet_get(self, l-1):
            #print "term=", self.term(), "l=", l, "doc=", doc, "DocSet_get(self, l-1)=", DocSet_get(self, l-1)
            raise Exception('non-increasing docid')
        DocSet_add(self._cobj, doc)

    def delete(self, doc):
        DocSet_remove(self, doc)

    def term(self):
        return DocSet_term(self)

    def releaseData(self):
        assert self._own_cobj, 'object already released, perhaps duplicate add()?'
        self._own_cobj = False;

    def combinedCardinality(self, rhs):
        return DocSet_combinedCardinality(self, rhs)

    def intersect(self, rhs):
        r = DocSet_intersect(self, rhs)
        return DocSet(cobj=r)
