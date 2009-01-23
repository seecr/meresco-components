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
from ctypes import c_uint32, c_int32, c_char_p, POINTER, cdll, pointer, py_object, Structure, c_ulong, c_int, c_float, cast
from docset import libDocSet

SELF = POINTER(None)

IntegerList_create = libDocSet.IntegerList_create
IntegerList_create.argtypes = [c_int]
IntegerList_create.restype = SELF

IntegerList_delete = libDocSet.IntegerList_delete
IntegerList_delete.argtypes = [SELF]
IntegerList_delete.restype = None

IntegerList_append = libDocSet.IntegerList_append
IntegerList_append.argtypes = [SELF, c_uint32]
IntegerList_append.restype = None

IntegerList_size = libDocSet.IntegerList_size
IntegerList_size.argtypes = [SELF]
IntegerList_size.restype = c_int

IntegerList_get = libDocSet.IntegerList_get
IntegerList_get.argtypes = [SELF, c_uint32]
IntegerList_get.restype = c_int32

IntegerList_set = libDocSet.IntegerList_set
IntegerList_set.argtypes = [SELF, c_int, c_uint32]
IntegerList_set.restype = None

IntegerList_delitems = libDocSet.IntegerList_delitems
IntegerList_delitems.argtypes = [SELF, c_int, c_int]
IntegerList_delitems.restype = None

IntegerList_slice = libDocSet.IntegerList_slice
IntegerList_slice.argtypes = [SELF, c_int, c_int, c_int]
IntegerList_slice.restype = SELF

IntegerList_mergeFromOffset = libDocSet.IntegerList_mergeFromOffset
IntegerList_mergeFromOffset.argtypes = [SELF, c_int]
IntegerList_mergeFromOffset.restype = c_int


class IntegerList(object):

    def __init__(self, size=0, cobj=None):
        if cobj:
            self._cobj = cobj
        else:
            self._cobj = IntegerList_create(size)
        self._as_parameter_ = self._cobj

    def __del__(self):
        pass
        #IntegerList_delete(self)

    def __len__(self):
        return IntegerList_size(self)

    def __getitem__(self, i):
        if type(i) == slice:
            start = i.start if i.start else 0
            step = i.step if i.step else 1
            stop = i.stop if i.stop else len(self)
            if start < 0:
                start = len(self) - -start
            islice = IntegerList_slice(self, start, stop, step)
            try:
                return list(IntegerList(cobj=islice))
            finally:
                IntegerList_delete(islice)

        return IntegerList_get(self, i)

    def __delitem__(self, i):
        if type(i) == slice:
            start = i.start if i.start else 0
            stop = i.stop if i.stop else len(self)
            IntegerList_delitems(self, start, stop)
        else:
            IntegerList_delitems(self, i, i+1)

    def __setitem__(self, index, value):
        IntegerList_set(self, index, value)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def append(self, integer):
        IntegerList_append(self, integer)

    def extend(self, aList):
        for i in aList:
            self.append(i)

    def __eq__(self, rhs):
        return self[:] == rhs[:]

    def copy(self):
        return IntegerList(cobj=IntegerList_slice(self, 0, len(self), 1))

    def mergeFromOffset(self, offset):
        return IntegerList_mergeFromOffset(self, offset)

    def getCObject(self):
        return self._cobj