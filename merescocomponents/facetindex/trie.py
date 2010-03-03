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
from ctypes import cdll, c_uint32, c_int, c_char_p, Structure, POINTER, pointer
from os.path import join, abspath, dirname
from libfacetindex import libFacetIndex as lib
from docset import DocSet
from integerlist import INTEGERLIST, IntegerList

class fwPtr(Structure):
    _fields_ = [ ('type', c_int, 2),
                 ('ptr', c_int, 30) ]

fwString = c_uint32

trie_init = lib.trie_init
trie_init.argtypes = None
trie_init.restype = None

trie_init()

fwValueNone = c_uint32.in_dll(lib, 'fwValueNone')

TrieNode_create = lib.TrieNode_create
TrieNode_create.argtypes = [ c_uint32 ]
TrieNode_create.restype = fwPtr

TrieNode_addValue2 = lib.TrieNode_addValue2
TrieNode_addValue2.argtypes = [ fwPtr, c_uint32, c_char_p ]
TrieNode_addValue2.restype = None

TrieNode_getValue2 = lib.TrieNode_getValue2
TrieNode_getValue2.argtypes = [ fwPtr, c_char_p ]
TrieNode_getValue2.restype = c_uint32

TrieNode_getValues2 = lib.TrieNode_getValues2
TrieNode_getValues2.argtypes = [ fwPtr, c_char_p, c_uint32, INTEGERLIST ]
TrieNode_getValues2.restype = None

TrieNode_printit2 = lib.TrieNode_printit2
TrieNode_printit2.argtypes = [ fwPtr, c_int ]
TrieNode_printit2.restype = None

nodecount = lib.nodecount
nodecount.argtypes = None
nodecount.restype = None


class Trie(object):

    def __init__(self):
        self._as_parameter_ = TrieNode_create(fwValueNone)

    def add(self, value, word):
        TrieNode_addValue2(self, value, word)

    def getValue(self, word, default=None):
        r = TrieNode_getValue2(self, word)
        if r == fwValueNone.value:
            return default
        return r

    def getValues(self, prefix, maxresults=maxint):
        result = IntegerList()
        TrieNode_getValues2(self, prefix, maxint, result)
        return result

    def printit(self):
        TrieNode_printit2(self, 0)

    def nodecount(self):
        nodecount()
