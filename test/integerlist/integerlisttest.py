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
# Copyright (C) 2011, 2013 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase
from time import time
from os import getpid, remove
from os.path import join, isfile

from meresco.components.integerlist import IntegerList

class IntegerListTest(SeecrTestCase):
    def testConstruct(self):
        l = IntegerList()
        self.assertEqual(0, len(l))
        l = IntegerList(10)
        self.assertEqual(10, len(l))
        self.assertEqual([0,1,2,3,4,5,6,7,8,9], list(l))

    def testAppend(self):
        l = IntegerList()
        l.append(4)
        self.assertEqual([4], list(l))
        l.append(8)
        self.assertEqual([4,8], list(l))

    def testLen(self):
        l = IntegerList()
        self.assertEqual(0, len(l))
        l.append(1)
        self.assertEqual(1, len(l))

    def testIndex(self):
        l = IntegerList(100)
        self.assertEqual(0, l[0])
        self.assertEqual(66, l[66])
        self.assertEqual(99, l[-1])
        self.assertEqual(98, l[-2])
        self.assertEqual(90, l[-10])

    def testSlicing(self):
        def assertSlice(expected, sliced):
            self.assertEqual(expected, sliced)
            self.assertEqual(len(expected), len(sliced))

        l = IntegerList(100)
        assertSlice([0,1], l[:2])
        assertSlice([1,2,3,4], l[1:5])
        assertSlice([98, 99], l[98:])
        assertSlice([98, 99], l[-2:])
        assertSlice([98], l[-2:99])
        assertSlice([], l[98:2])
        assertSlice([0], l[-200:1])
        assertSlice(list(range(99)), l[-200:-1])
        assertSlice(list(range(100)), l[-200:200])
        assertSlice([], l[0:0])
        assertSlice(list(range(100)), l[:])
        self.assertRaises(ValueError, lambda: l[::-1])
        assertSlice(list(range(98)), l[-200:-1][:-1])

    def testCopySlice(self):
        l = IntegerList(100)
        m = l[:]
        self.assertEqual(100, len(m))

    def testExtend(self):
        l = IntegerList()
        l.extend([1,2])
        self.assertEqual(2, len(l))
        self.assertEqual([1,2], list(l))
        l.extend([3,4])
        self.assertEqual(4, len(l))
        self.assertEqual([1,2,3,4], list(l))

    def testDel(self):
        l = IntegerList()
        try:
            del l[0]
            self.fail()
        except IndexError as e:
            self.assertEqual("list assignment index out of range", str(e))
        l.extend([-1,1,2,3,4])
        del l[1]
        self.assertEqual(4, len(l))
        self.assertEqual([-1,2,3,4], list(l))
        try:
            del l[4]
            self.fail()
        except IndexError as e:
            self.assertEqual("list assignment index out of range", str(e))
        del l[-1]
        self.assertEqual([-1,2,3], list(l))
        del l[1]
        self.assertEqual([-1,3], list(l))

    def testDelSlice(self):
        l = IntegerList()
        del l[0:]
        l = IntegerList(10)
        del l[5:]
        self.assertEqual([0,1,2,3,4], list(l))
        del l[6:]
        self.assertEqual([0,1,2,3,4], list(l))
        del l[3:]
        self.assertEqual([0,1,2], list(l))

    def testRandomDel(self):
        l = IntegerList()
        l.extend(list(range(10)))
        del l[2]
        del l[6]
        del l[4]
        self.assertEqual([0,1,3,4,6,8,9], list(l))

        l = IntegerList()
        l.extend(list(range(10)))
        del l[2:4]
        self.assertEqual([0,1,4,5,6,7,8,9], list(l))
        del l[3:5]
        self.assertEqual([0,1,4,7,8,9], list(l))
        del l[2:4]
        self.assertEqual([0,1,8,9], list(l))

        l.save(self.tempdir+'/list.bin', offset=0)
        l2 = IntegerList()
        l2.extendFrom(self.tempdir+'/list.bin')
        self.assertEqual([0,1,8,9], l2)

        del l[1:3]
        self.assertEqual([0, 9], list(l))
        l.save(self.tempdir+'/list.bin', offset=0)
        l2 = IntegerList()
        l2.extendFrom(self.tempdir+'/list.bin')
        self.assertEqual([0, 9], l2)

    def testEquality(self):
        l1 = IntegerList(10)
        l2 = IntegerList(10)
        self.assertEqual(l1, l2)
        l3 = IntegerList(10)
        self.assertEqual(l1, l3)

    def testCopy(self):
        l = IntegerList(5)
        copy = l.copy()
        self.assertEqual([0,1,2,3,4], list(l))
        self.assertEqual(5, len(copy))
        self.assertEqual([0,1,2,3,4], list(copy))
        l.append(9)
        copy.append(7)
        self.assertEqual([0,1,2,3,4, 9], list(l))
        self.assertEqual([0,1,2,3,4, 7], list(copy))

    def testSetItem(self):
        l = IntegerList(5)
        l[0] = 10
        l[2] = -1
        self.assertEqual([10,1,-1,3,4], list(l))

    def testSetItemAfterDelete(self):
        l = IntegerList()
        l.extend(list(range(5)))
        self.assertEqual([0,1,2,3,4], list(l))
        del l[2]
        self.assertEqual([0,1,3,4], list(l))
        l[2] = 2
        self.assertEqual([0,1,2,4], list(l))

    def testIndexBoundaryCheck(self):
        l = IntegerList(5)
        try:
            l[0]
            l[1]
            l[2]
            l[3]
            l[4]
            l[5]
            self.fail('must raise exception')
        except Exception as e:
            self.assertEqual('5', str(e))
        try:
            l[-1]
            l[-2]
            l[-3]
            l[-4]
            l[-5]
            l[-6]
            self.fail('must raise exception')
        except Exception as e:
            self.assertEqual('-6', str(e))

    def testSave(self):
        l1 = IntegerList(5)
        l1.save(self.tempdir+'/list.bin')
        l2 = IntegerList()
        l2.extendFrom(self.tempdir+'/list.bin')
        self.assertEqual(l1, l2)
        l2.extendFrom(self.tempdir+'/list.bin')
        self.assertEqual([0,1,2,3,4,0,1,2,3,4], l2)

    def testSaveFromOffset(self):
        l1 = IntegerList(5)
        l1.save(self.tempdir+'/list.bin', offset=3)
        l2 = IntegerList()
        l2.extendFrom(self.tempdir+'/list.bin')
        self.assertEqual([3,4], l2)

    def testSaveInvalidOffset(self):
        l1 = IntegerList(5)
        try:
            l1.save(self.tempdir+'/list.bin', offset=5)
            self.fail()
        except Exception as e:
            self.assertEqual('Invalid index: 5 [0..5)', str(e))
        try:
            l1.save(self.tempdir+'/list.bin', offset=-1)
            self.fail()
        except Exception as e:
            self.assertEqual('Invalid index: -1 [0..5)', str(e))

    def testSaveEmpty(self):
        l = IntegerList()
        l.save(self.tempdir+'/empty')
        l.extendFrom(self.tempdir+'/empty')
        self.assertEqual([], l)

    def testSaveWrongDir(self):
        l1 = IntegerList(5)
        try:
            l1.save(self.tempdir + '/notexist/doesnotexist')
            self.fail('must raise ioerror')
        except IOError as e:
            self.assertTrue("[Errno 2] No such file or directory:" in str(e), str(e))

    def testSaveWithDeletes(self):
        l = IntegerList()
        l.extend([-1,1,2,3])
        del l[1:3]
        self.assertEqual([-1,3], list(l))
        l.save(self.tempdir+'/ilist')
        l = IntegerList()
        l.extendFrom(self.tempdir+'/ilist')
        self.assertEqual([-1,3], list(l))

    def testSaveOffsetWithDeletes(self):
        l = IntegerList()
        l.extend([1,2,3])
        del l[0]
        self.assertEqual([2,3], list(l))
        l.save(self.tempdir+'/ilist', offset=0)
        l = IntegerList()
        l.extendFrom(self.tempdir+'/ilist')
        self.assertEqual([2,3], list(l))

    def testLoadWrongDir(self):
        l1 = IntegerList(5)
        try:
            l1.extendFrom(self.tempdir + '/doesnotexist')
            self.fail('must raise ioerror')
        except IOError as e:
            self.assertTrue("[Errno 2] No such file or directory" in str(e), str(e))
        self.assertEqual([0,1,2,3,4], list(l1))

    def testSaveAppend(self):
        filepath = join(self.tempdir, 'list.bin')
        def check(expected):
            l2 = IntegerList()
            l2.extendFrom(filepath)
            self.assertEqual(expected, l2)

        if isfile(filepath):
            remove(filepath)
        l1 = IntegerList()
        l1.save(filepath, append=True)
        check([])

        l1 = IntegerList()
        l1.append(94)
        l1.append(34)
        l1.append(81)

        l1.save(filepath, append=True)
        check([94, 34, 81])

        l1 = IntegerList()
        l1.append(8)
        l1.append(4)
        l1.append(16)

        l1.save(filepath, offset=1, append=True)
        check([94, 34, 81, 4, 16])

    def testNoMemoryLeakInIntegerlist(self):
        self.probeMemory() 
        for i in range(100):
            l1 = IntegerList(1000000)
            l2 = IntegerList(1000000)
        l1 = None
        l2 = None
        self.assertNoMemoryLeaks()

    def testDeleteAlls(self):
        l = IntegerList()
        l.extend(list(range(10)))
        for x in range(10):
            del l[0]
        self.assertEqual([], list(l))

    def testIntegerSizes(self):
        l = IntegerList(0)
        l.append(2 ** 63 - 2)
        l.append(2 ** 64 - 1)
        l.append(2 ** 64)
        self.assertEqual([2 ** 63 - 2, -1, 0], l)

    def testIter(self):
        il = IntegerList(10 ** 5)
        t0 = time()
        for x in il:
            pass
        t1 = time()
        self.assertTiming(0.28, t1 - t0, 0.55)

    def testIterWhileModifyingList(self):
        il = IntegerList()
        il.extend([1,2,3,4])
        i = iter(il)
        numbers = []
        numbers.append(next(i))
        numbers.append(next(i))
        del il[0]
        numbers.append(next(i))
        self.assertRaises(StopIteration, i.__next__)
        self.assertEqual([1,2,4], numbers)
        self.assertEqual([2,3,4], il)

        # 3 is not returned, although still in the list
        # this is default python behaviour

        l = [1,2,3,4]
        i = iter(l)
        numbers = []
        numbers.append(next(i))
        numbers.append(next(i))
        del l[0]
        numbers.append(next(i))
        self.assertRaises(StopIteration, i.__next__)
        self.assertEqual([1,2,4], numbers)
        self.assertEqual([2,3,4], l)


    def testIterateOnSliceWhileModifyingList(self):
        il = IntegerList()
        il.extend([1,2,3,4])
        self.assertEqual([1,2,3,4], list(il[:]))
        slice = iter(il[:])
        numbers = []
        numbers.append(next(slice))
        numbers.append(next(slice))
        del il[0]
        il.append(5)
        del il[1]
        il.append(6)
        numbers.append(next(slice))
        numbers.append(next(slice))
        self.assertEqual([2,4,5,6], list(il[:]))
        self.assertEqual([1,2,3,4], numbers)


    def testSlicingPerformance(self):
        il = IntegerList(10 ** 7)
        t0 = time()
        segment = il[:][:10]
        t1 = time()
        self.assertTiming(0.04, t1 - t0, 0.08)

    def testSetMaxInt(self):
        il = IntegerList()
        il.append(2 ** 63 - 2)
        il.append(2 ** 63 - 1)
        il.save(join(self.tempdir, 'ilist'))
        il = IntegerList()
        il.extendFrom(join(self.tempdir, 'ilist'))
        self.assertEqual([2 ** 63 - 2], list(il))

    def testSaveFromOffsetWithDelete(self):
        filename = join(self.tempdir, 'list')
        il = IntegerList()
        il.append(1)
        il.append(2)
        il.save(filename, offset=0)
        del il[0]
        il.append(3)
        il.save(filename, offset=1, append=True)
        self.assertEqual([2,3], list(il))

        il = IntegerList()
        il.extendFrom(filename)
        self.assertEqual([1,2,3], list(il))

    def probeMemory(self):
        self.vmsize = self._getVmSize()

    def _getVmSize(self):
        status = open('/proc/%d/status' % getpid()).read()
        i = status.find('VmSize:') + len('VmSize:')
        j = status.find('kB', i)
        vmsize = int(status[i:j].strip())
        return vmsize

    def assertNoMemoryLeaks(self, bandwidth=0.8):
        vmsize = self._getVmSize()
        self.assertTrue(self.vmsize*bandwidth < vmsize < self.vmsize/bandwidth,
                "memory leaking: before: %d, after: %d" % (self.vmsize, vmsize))



