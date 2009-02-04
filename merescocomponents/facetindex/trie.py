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
from ctypes import cdll, c_uint32, c_int, c_char_p, Structure, POINTER, pointer
from os.path import join, abspath, dirname
from libfacetindex import libFacetIndex as lib
from docset import DocSet

#lib = cdll.LoadLibrary(join(abspath(dirname(__file__)), '_facetindex.so'))

class fwPtr(Structure):
    _fields_ = [ ('type', c_int, 2),
                 ('ptr', c_int, 30) ]

fwString = c_uint32

trie_init = lib.trie_init
trie_init.argtypes = None
trie_init.restype = None

fwString_init = lib.fwString_init
fwString_init.argtypes = None
fwString_init.restype = None

fwString_init()
trie_init()

fwValueNone = c_uint32.in_dll(lib, 'fwValueNone')

fwString_create = lib.fwString_create
fwString_create.argtypes = [ c_char_p ]
fwString_create.restype = fwString

fwString_get = lib.fwString_get
fwString_get.argtypes = [ fwString ]
fwString_get.restype = c_char_p

TrieNode_create = lib.TrieNode_create
TrieNode_create.argtypes = [ c_uint32 ]
TrieNode_create.restype = fwPtr

TrieNode_addValue = lib.TrieNode_addValue
TrieNode_addValue.argtypes = [ fwPtr, c_uint32, fwString, POINTER(None) ]
TrieNode_addValue.restype = None

TrieNode_getValue = lib.TrieNode_getValue
TrieNode_getValue.argtypes = [ fwPtr, c_char_p, POINTER(None) ]
TrieNode_getValue.restype = c_uint32

TrieNode_getValues = lib.TrieNode_getValues
TrieNode_getValues.argtypes = [fwPtr, c_char_p, POINTER(None), c_int]
TrieNode_getValues.restype = None

TrieNode_printit = lib.TrieNode_printit
TrieNode_printit.argtypes = [ fwPtr, c_int ]
TrieNode_printit.restype = None

nodecount = lib.nodecount
nodecount.argtypes = None
nodecount.restype = None

class Trie:

    def __init__(self):
        self._as_parameter_ = TrieNode_create(fwValueNone)
        self._temp_value2fwstr = {}

    def add(self, value, word):
        termnr = fwString_create(word)
        self._temp_value2fwstr[value] = termnr
        TrieNode_addValue(self, value, termnr, 0)

    def getValue(self, word, default=None):
        r = TrieNode_getValue(self, word, 0)
        if r == fwValueNone.value:
            return default
        return r

    def getTerm(self, value):
        fwstr = self._temp_value2fwstr[value]
        return fwString_get(fwstr)

    def getValues(self, prefix, caseSensitive=True):
        result = DocSet()
        TrieNode_getValues(self, prefix, result, caseSensitive)
        return result

    def printit(self):
        TrieNode_printit(self, 0)

    def nodecount(self):
        nodecount()
