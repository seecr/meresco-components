# -*- coding: utf-8 -*-
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

from cq2utils import CQ2TestCase
from time import time
from os import getpid, remove
from os.path import join, isfile

from meresco.components.facetindex import IntegerList

class IntegerListTest(CQ2TestCase):
    def testConstruct(self):
        l = IntegerList()
        self.assertEquals(0, len(l))
        l = IntegerList(10)
        self.assertEquals(10, len(l))
        self.assertEquals([0,1,2,3,4,5,6,7,8,9], list(l))

    def testConstruct64(self):
        l = IntegerList(use64bits=True)
        self.assertEquals(0, len(l))
        l = IntegerList(10, use64bits=True)
        self.assertEquals(10, len(l))
        self.assertEquals([0,1,2,3,4,5,6,7,8,9], list(l))

    def testAppend(self):
        for l in [IntegerList(), IntegerList(use64bits=True)]:
            l.append(4)
            self.assertEquals([4], list(l))
            l.append(8)
            self.assertEquals([4,8], list(l))

    def testLen(self):
        for l in [IntegerList(), IntegerList(use64bits=True)]:
            self.assertEquals(0, len(l))
            l.append(1)
            self.assertEquals(1, len(l))

    def testIndex(self):
        for l in [IntegerList(100), IntegerList(100, use64bits=True)]:
            self.assertEquals(0, l[0])
            self.assertEquals(66, l[66])
            self.assertEquals(99, l[-1])
            self.assertEquals(98, l[-2])
            self.assertEquals(90, l[-10])

    def testSlicing(self):
        def assertSlice(expected, sliced):
            self.assertEquals(expected, sliced)
            self.assertEquals(len(expected), len(sliced))

        for l in [IntegerList(100), IntegerList(100, use64bits=True)]:
            assertSlice([0,1], l[:2])
            assertSlice([1,2,3,4], l[1:5])
            assertSlice([98, 99], l[98:])
            assertSlice([98, 99], l[-2:])
            assertSlice([98], l[-2:99])
            assertSlice([], l[98:2])
            assertSlice([0], l[-200:1])
            assertSlice(range(99), l[-200:-1])
            assertSlice(range(100), l[-200:200])
            assertSlice([], l[0:0])
            assertSlice(range(100), l[:])
            self.assertRaises(ValueError, lambda: l[::-1])
            assertSlice(range(98), l[-200:-1][:-1])

    def testSlicesImmutable(self):
        s = IntegerList(100)[1:5]
        self.assertRaises(AttributeError, lambda: s.append(101))
        self.assertRaises(AttributeError, lambda: s.extend([101]))
        try:
            del s[0]
            self.fail('del should have failed.')
        except TypeError, e:
            pass
        try:
            s[0] = 200
            self.fail('assignment should have failed.')
        except TypeError, e:
            pass

    def testCopySlice(self):
        for l in [IntegerList(100), IntegerList(100, use64bits=True)]:
            m = l[:]
            self.assertEquals(100, len(m))

    def testExtend(self):
        for l in [IntegerList(), IntegerList(use64bits=True)]:
            l.extend([1,2])
            self.assertEquals(2, len(l))
            self.assertEquals([1,2], list(l))
            l.extend([3,4])
            self.assertEquals(4, len(l))
            self.assertEquals([1,2,3,4], list(l))

    def testDel(self):
        for use64bits in [False, True]:
            l = IntegerList(use64bits=use64bits)
            try:
                del l[0]
                self.fail()
            except IndexError, e:
                self.assertEquals("list assignment index out of range", str(e))
            l.extend([1,2])
            del l[0]
            self.assertEquals(1, len(l))
            self.assertEquals([2], list(l))
            try:
                del l[1]
                self.fail()
            except IndexError, e:
                self.assertEquals("list assignment index out of range", str(e))
            del l[-1]
            self.assertEquals([], list(l))

    def testDelSlice(self):
        for use64bits in [False, True]:
            l = IntegerList(use64bits=use64bits)
            del l[0:]
            l = IntegerList(10, use64bits=use64bits)
            del l[5:]
            self.assertEquals([0,1,2,3,4], list(l))
            del l[6:]
            self.assertEquals([0,1,2,3,4], list(l))

    def testEquality(self):
        l1 = IntegerList(10)
        l2 = IntegerList(10)
        self.assertEquals(l1, l2)
        l3 = IntegerList(10, use64bits=True)
        self.assertEquals(l1, l3)

    def testCopy(self):
        for l in [IntegerList(5), IntegerList(5, use64bits=True)]:
            copy = l.copy()
            self.assertEquals([0,1,2,3,4], list(l))
            self.assertEquals(5, len(copy))
            self.assertEquals([0,1,2,3,4], list(copy))
            l.append(9)
            copy.append(7)
            self.assertEquals([0,1,2,3,4, 9], list(l))
            self.assertEquals([0,1,2,3,4, 7], list(copy))

    def testSetItem(self):
        for l in [IntegerList(5), IntegerList(5, use64bits=True)]:
            l[0] = 10
            l[2] = -1
            self.assertEquals([10,1,-1,3,4], list(l))

    def testDitchHolesStartingAt(self):
        for use64bits in [False, True]:
            l = IntegerList(5, use64bits=use64bits)
            l.mergeFromOffset(0)
            self.assertEquals([0,1,2,3,4], list(l))

            l = IntegerList(5, use64bits=use64bits)
            l[2] = -3
            l[4] = -5
            l.mergeFromOffset(0)
            self.assertEquals([0,1,3], list(l))

            l = IntegerList(5, use64bits=use64bits)
            l[2] = -3
            l[4] = -5
            l.mergeFromOffset(3)
            self.assertEquals([0,1,-3,3], list(l))

            l = IntegerList(5, use64bits=use64bits)
            for i in range(5):
                l[i] = i ^ -1
            l.mergeFromOffset(0)
            self.assertEquals([], list(l))

            l = IntegerList(5, use64bits=use64bits)
            l[2] = -3
            l.mergeFromOffset(2)
            self.assertEquals([0, 1, 3, 4], list(l))

    def testIndexBoundaryCheck(self):
        for use64bits in [False, True]:
            l = IntegerList(5, use64bits=use64bits)
            try:
                l[0]
                l[1]
                l[2]
                l[3]
                l[4]
                l[5]
                self.fail('must raise exception')
            except Exception, e:
                self.assertEquals('5', str(e))
            try:
                l[-1]
                l[-2]
                l[-3]
                l[-4]
                l[-5]
                l[-6]
                self.fail('must raise exception')
            except Exception, e:
                self.assertEquals('-6', str(e))

    def testSave(self):
        for use64bits in [False, True]:
            l1 = IntegerList(5, use64bits=use64bits)
            l1.save(self.tempdir+'/list.bin')
            l2 = IntegerList(use64bits=use64bits)
            l2.extendFrom(self.tempdir+'/list.bin')
            self.assertEquals(l1, l2)
            l2.extendFrom(self.tempdir+'/list.bin')
            self.assertEquals([0,1,2,3,4,0,1,2,3,4], l2)

    def testSaveFromOffset(self):
        for use64bits in [False, True]:
            l1 = IntegerList(5, use64bits=use64bits)
            l1.save(self.tempdir+'/list.bin', offset=3)
            l2 = IntegerList(use64bits=use64bits)
            l2.extendFrom(self.tempdir+'/list.bin')
            self.assertEquals([3,4], l2)

    def testSaveInvalidOffset(self):
        for use64bits in [False, True]:
            l1 = IntegerList(5, use64bits=use64bits)
            try:
                l1.save(self.tempdir+'/list.bin', offset=5)
                self.fail()
            except Exception, e:
                self.assertEquals('Invalid index: 5 [0..5)', str(e))
            try:
                l1.save(self.tempdir+'/list.bin', offset=-1)
                self.fail()
            except Exception, e:
                self.assertEquals('Invalid index: -1 [0..5)', str(e))

    def testSaveEmpty(self):
        for use64bits in [False, True]:
            l = IntegerList(use64bits=use64bits)
            l.save(self.tempdir+'/empty')
            l.extendFrom(self.tempdir+'/empty')
            self.assertEquals([], l)

    def testSaveWrongDir(self):
        for use64bits in [False, True]:
            l1 = IntegerList(5, use64bits=use64bits)
            try:
                l1.save(self.tempdir + '/notexist/doesnotexist')
                self.fail('must raise ioerror')
            except IOError, e:
                self.assertTrue("[Errno 2] No such file or directory:" in str(e), str(e))

    def testLoadWrongDir(self):
        for use64bits in [False, True]:
            l1 = IntegerList(5, use64bits=use64bits)
            try:
                l1.extendFrom(self.tempdir + '/doesnotexist')
                self.fail('must raise ioerror')
            except IOError, e:
                self.assertTrue("[Errno 2] No such file or directory" in str(e), str(e))
            self.assertEquals([0,1,2,3,4], list(l1))

    def testSaveAppend(self):
        filepath = join(self.tempdir, 'list.bin')
        for use64bits in [False, True]:
            def check(expected):
                l2 = IntegerList(use64bits=use64bits)
                l2.extendFrom(filepath)
                self.assertEquals(expected, l2)

            if isfile(filepath):
                remove(filepath)
            l1 = IntegerList(use64bits=use64bits)
            l1.save(filepath, append=True)
            check([])

            l1 = IntegerList(use64bits=use64bits)
            l1.append(94)
            l1.append(34)
            l1.append(81)

            l1.save(filepath, append=True)
            check([94, 34, 81])

            l1 = IntegerList(use64bits=use64bits)
            l1.append(8)
            l1.append(4)
            l1.append(16)

            l1.save(filepath, offset=1, append=True)
            check([94, 34, 81, 4, 16])

    def testNoMemoryLeakInIntegerlist(self):
        self.probeMemory() 
        for i in range(100):
            l1 = IntegerList(1000000)
            l2 = IntegerList(1000000, use64bits=True)
        l1 = None
        l2 = None
        self.assertNoMemoryLeaks()

    def testIntegerSizes(self):
        l = IntegerList(0, use64bits=False)
        l.append(2 ** 31 - 1)
        l.append(2 ** 32 - 1)
        l.append(2 ** 32)
        self.assertEquals([2 ** 31 - 1, -1, 0], l)

        l = IntegerList(0, use64bits=True)
        l.append(2 ** 63 - 1)
        l.append(2 ** 64 - 1)
        l.append(2 ** 64)
        self.assertEquals([2 ** 63 - 1, -1, 0], l)

    def testIter(self):
        il = IntegerList(10 ** 5)
        t0 = time()
        for x in il:
            pass
        t1 = time()
        self.assertTiming(0.15, t1 - t0, 0.25)

    def testSlicingPerformance(self):
        il = IntegerList(10 ** 7)
        t0 = time()
        segment = il[:][:10]
        t1 = time()
        self.assertTiming(0.00, t1 - t0, 0.001)

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



