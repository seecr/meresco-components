from unittest import TestCase

from merescocomponents.facetindex.libfacetindex import libFacetIndex, c_method, c_wrapper, mangle
from merescocomponents.facetindex.docset import DOCSET
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
