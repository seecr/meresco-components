## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
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
from unittest import TestCase

from meresco.components.facetindex.libfacetindex import libFacetIndex, c_method, c_wrapper, mangle
from meresco.components.facetindex.docset import DOCSET
from ctypes import c_uint, c_uint32, Structure, c_int, POINTER

class LibFacetIndexTest(TestCase):
    def testDecorator(self):

        class DocSet(object):
            c_type = POINTER(None)

            def __init__(self, c_obj):
                self._as_parameter_ = c_obj

            @classmethod
            @c_method(argtypes=(DOCSET,), restype=POINTER(None))
            def from_param(clazz, obj):
                pass

            @classmethod
            @c_wrapper(argtypes=(c_int,), restype=DOCSET)
            def create(clazz, c_funct, *args, **kwargs):
                c_obj = c_funct(*args, **kwargs)
                return DocSet(c_obj)

            @classmethod
            @c_wrapper(argtypes=(c_int,), restype=DOCSET)
            def forTesting(clazz, c_funct, *args, **kwargs):
                c_obj = c_funct(*args, **kwargs)
                return DocSet(c_obj)

            @c_method(argtypes=(c_uint32,), restype=c_int)
            def contains(self, value):
                pass

        x = DocSet.create(10)
        self.assertEquals(False, x.contains(1))
        x = DocSet.forTesting(3)
        self.assertEquals(True, x.contains(0))
        self.assertEquals(True, x.contains(1))
        self.assertEquals(True, x.contains(2))
        self.assertEquals(False, x.contains(3))

    def testUseMangledNamesDirectlyWithoutCppWrapper(self):
        class DocSet(object):
            c_type = POINTER(None)

            @c_method(argtypes=(), restype=POINTER(None))
            def from_param(self):
                pass

            def __init__(self, c_obj):
                self._as_parameter_ = c_obj

            @classmethod
            @c_wrapper(argtypes=(c_int,), restype=POINTER(None))
            def create2(clazz, c_funct, *args, **kwargs):
                c_obj = c_funct(*args, **kwargs)
                return DocSet(c_obj)

        d = DocSet.create2(0)
        m = libFacetIndex._ZN6DocSet8containsEj
        m.argtypes = [POINTER(None), c_uint32]
        m.restype = c_int
        r = m(d, 4)
        self.assertEquals(0, r)
        self.assertEquals('_ZN6DocSet8containsEj', mangle(('DocSet','contains'),(c_uint,)))
