
from libfacetindex import libFacetIndex
from ctypes import POINTER
from cq2utils import deallocator

TRIEDICT = POINTER(None)

TrieDict_create = libFacetIndex.TrieDict_create
TrieDict_create.argtypes = []
TrieDict_create.restype = TRIEDICT

TrieDict_delete = libFacetIndex.TrieDict_delete
TrieDict_delete.argtypes = [TRIEDICT]
TrieDict_delete.restype = None


class TrieDict(object):
    def __init__(self):
        self._cobj = TrieDict_create()
        self._dealloc = deallocator(TrieDict_delete, self._cobj)
        self._as_parameter_ = self._cobj
        