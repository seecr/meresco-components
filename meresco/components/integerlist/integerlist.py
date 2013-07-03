# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2011 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2011-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
#
# This file is part of "Meresco Components"
#
# "Meresco Components" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Components" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Components"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from ctypes import c_uint64, c_int64, c_char_p, POINTER, c_int
from libintegerlist import libIntegerList

INTEGERLIST = POINTER(None)

IntegerList_create = libIntegerList.IntegerList_create
IntegerList_create.argtypes = [c_int]
IntegerList_create.restype = INTEGERLIST

IntegerList_delete = libIntegerList.IntegerList_delete
IntegerList_delete.argtypes = [INTEGERLIST]
IntegerList_delete.restype = None

IntegerList_append = libIntegerList.IntegerList_append
IntegerList_append.argtypes = [INTEGERLIST, c_uint64]
IntegerList_append.restype = None

IntegerList_size = libIntegerList.IntegerList_size
IntegerList_size.argtypes = [INTEGERLIST]
IntegerList_size.restype = c_int

IntegerList_get = libIntegerList.IntegerList_get
IntegerList_get.argtypes = [INTEGERLIST, c_uint64]
IntegerList_get.restype = c_int64

IntegerList_set = libIntegerList.IntegerList_set
IntegerList_set.argtypes = [INTEGERLIST, c_int, c_uint64]
IntegerList_set.restype = None

IntegerList_delitems = libIntegerList.IntegerList_delitems
IntegerList_delitems.argtypes = [INTEGERLIST, c_int, c_int]
IntegerList_delitems.restype = None

IntegerList_slice = libIntegerList.IntegerList_slice
IntegerList_slice.argtypes = [INTEGERLIST, c_int, c_int]
IntegerList_slice.restype = INTEGERLIST

IntegerList_save = libIntegerList.IntegerList_save
IntegerList_save.argtypes = [INTEGERLIST, c_char_p, c_int, c_int]
IntegerList_save.restype = c_int

IntegerList_extendFrom = libIntegerList.IntegerList_extendFrom
IntegerList_extendFrom.argtypes = [INTEGERLIST, c_char_p]
IntegerList_extendFrom.restype = c_int


class IntegerList(object):
    def __init__(self, size=0, cobj=None):
        if cobj:
            self._cobj = cobj
        else:
            self._cobj = IntegerList_create(size)
        self._as_parameter_ = self._cobj

    def __del__(self):
        IntegerList_delete(self._cobj)

    def __len__(self):
        return IntegerList_size(self)

    def __getitem__(self, i):
        length = len(self)
        if type(i) == slice:
            start, stop = self._parseSlice(i)
            islice = IntegerList_slice(self, start, stop)
            return IntegerList(cobj=islice)
        if i >= length or -i > length:
            raise IndexError(i)
        return IntegerList_get(self, i)

    def __delitem__(self, i):
        if type(i) == slice:
            start, stop = self._parseSlice(i)
            IntegerList_delitems(self, start, stop)
        else:
            length = len(self)
            if i < 0:
                i = length - -i
            if i >= length or i < 0:
                raise IndexError("list assignment index out of range")
            IntegerList_delitems(self, i, i+1)

    def _parseSlice(self, slice, length=None):
        if not slice.step in [None, 1]:
            raise ValueError("%s does not support stepping slices" % self.__class__.__name__)
        start, stop, ignored = slice.indices(length or IntegerList_size(self))
        return start, stop

    def __setitem__(self, index, value):
        IntegerList_set(self, index, value)

    def __iter__(self):
        i = 0
        while i < IntegerList_size(self):
            yield IntegerList_get(self, i)
            i += 1

    def append(self, integer):
        IntegerList_append(self, integer)

    def extend(self, aList):
        for i in aList:
            self.append(i)

    def __eq__(self, rhs):
        return list(self) == list(rhs)

    def __repr__(self):
        return repr(list(i for i in self))

    def copy(self):
        return IntegerList(cobj=IntegerList_slice(self, 0, len(self), 1))

    def getCObject(self):
        return self._cobj

    def save(self, filename, offset=0, append=False):
        errno = IntegerList_save(self, filename, offset, append)
        if errno == -1:
            raise IndexError("Invalid index: %d [0..%d)" % (offset, len(self)))
        if errno:
            raise IOError("[Errno %d] No such file or directory: '%s'" % (errno, filename))

    def extendFrom(self, filename):
        errno = IntegerList_extendFrom(self, filename)
        if errno:
            raise IOError("[Errno %d] No such file or directory: '%s'" % (errno, filename))

