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
from unittest import TestCase
from ctypes import c_int, c_uint, c_short, Structure
from merescocomponents.facetindex.docset import DocSet, libDocSet as lib

fwPool = c_int
class fwPtr(Structure):
    _fields_ = [ ('type', c_uint, 2),
                 ('ptr', c_uint, 30) ]

pool_init = lib.pool_init
pool_init.argtypes = None
pool_init.restype = None
pool_init();

#fwPool Pool_create(short elementType, size_t elementSize, int initialSize);
Pool_create = lib.Pool_create
Pool_create.argtypes = [ c_short, c_int, c_int ]
Pool_create.restype = fwPool

#fwPtr Pool_new(fwPool self);
Pool_new = lib.Pool_new
Pool_new.argtypes = [ fwPool ]
Pool_new.restype = fwPtr

Pool_free = lib.Pool_free
Pool_free.argtypes = [ fwPool, fwPtr ]
Pool_free.restype = None

class Pool:
    def __init__(self, elementType, elementSize, initialSize):
        self._as_parameter_ = Pool_create(elementType, elementSize, initialSize)
    def new(self):
        return Pool_new(self)
    def free(self, x):
        Pool_free(self, x)

class PoolTest(TestCase):

    def testCreate(self):
        pool1 = Pool(1, 10, 10)
        self.assertEquals(5, pool1._as_parameter_)
        pool2 = Pool(2, 10, 10)
        self.assertEquals(6, pool2._as_parameter_)
        pool3 = Pool(3, 10, 10)
        self.assertEquals(7, pool3._as_parameter_)
        pool4 = Pool(4, 10, 10)
        self.assertEquals(8, pool4._as_parameter_)

    def testNewItem(self):
        pool = Pool(3, 0, 10)
        object = pool.new()
        self.assertEquals(3, object.type)
        self.assertEquals(0, object.ptr)

    def XXXXXXXXXXXXXXXXXtestFillEachObjectStateCompletelyForceReallocAndTestAllStates(self):
        poolSize = 10000
        elementSize = 12
        elementType = 1
        refs = []
        pool = Pool(elementType, elementSize, poolSize)
        words = [word.strip() for word in open('words') if len(word.strip()) >= elementSize]
        for i in range(poolSize-1):
            X = pool.newFilledWith(words[i])
            refs.append(X)
        for i in range(poolSize-1):
            self.assertEquals(words[i][:elementSize-1], pool.get(refs[i]), (words[i],  pool.get(refs[i]), i))

    def testRecycle(self):
        pool = Pool(elementType=1, elementSize=10, initialSize=100)
        obj1 = pool.new()
        pool.free(obj1)
        obj2 = pool.new()
        self.assertEquals(obj1.ptr, obj2.ptr)

    def testRecycleListExpandsIfNeeded(self):
        pool = Pool(elementType=1, elementSize=10, initialSize=10)
        pointers = []
        for i in range(20):
            ptr = pool.new()
            pointers.append(ptr)
        for i in range(20):
            pool.free(pointers[i])

        pointers.reverse()
        for i in range(20):
            ptr = pool.new()
            self.assertEquals(pointers[i].ptr, ptr.ptr, (pointers, ptr,i) )
