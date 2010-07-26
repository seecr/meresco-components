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

from __future__ import with_statement
from cq2utils import CQ2TestCase
from os.path import join
from bisect import bisect_left, bisect_right

from merescocomponents import SortedFileList, FileList
from merescocomponents.packer import IntStringPacker, IntPacker
from time import time

class FileListTest(CQ2TestCase):
    def testAppendAndWrite(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        s.append(1)
        s.append(2)
        self.assertEquals([1,2], list(iter(s)))
        self.assertEquals(16, len(open(join(self.tempdir, 'list')).read()))
        self.assertEquals([1,2], list(s))
        s = SortedFileList(join(self.tempdir, 'list'))
        self.assertEquals([1,2], list(iter(s)))
        self.assertEquals(len(s), len(list(s)))

    def testRewrite(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        for i in range(20):
            s.append(i)
        s = SortedFileList(join(self.tempdir, 'list'), (i for i in s if i%2 == 0))
        self.assertEquals([0,2,4,6,8,10,12,14,16,18], list(s))
        self.assertEquals(len(s), len(list(s)))

    def testEmpty(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        self.assertEquals([], list(s))

    def testContains(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        for i in range(0,20,2):
            s.append(i)
        self.assertTrue(14 in s)
        self.assertFalse(15 in s)
        self.assertFalse(32 in s)

    def testZero(self):
        s = FileList(join(self.tempdir, 'list'))
        s.append(0)
        self.assertEquals([0],list(s))

    def testGetItem(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        for i in range(20):
            s.append(i)
        self.assertEquals(2, s[2])
        self.assertIndexError(s, 1234567)
        self.assertEquals(19, s[-1])
        self.assertEquals(0, s[-20])
        self.assertIndexError(s, -21)

    def testSlicing(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        for i in range(6):
            s.append(i)
        self.assertEquals([], list(s[0:0]))
        self.assertEquals([1,2], list(s[1:3]))
        self.assertEquals([0,1,2,3], list(s[:-2]))
        self.assertEquals([4,5], list(s[-2:]))
        self.assertEquals([0,2], list(s[:4:2]))
        self.assertEquals([5,4,3,2,1,0], list(s[::-1]))
        self.assertEquals([], list(s[4:3]))
        self.assertEquals([0,1,2,3,4,5], list(s[-12345:234567]))
        self.assertEquals([1,2], list(s[1:3]))

    def testSlicingCreatesASequence(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        for i in range(6):
            s.append(i)
        r = s[2:4]
        self.assertEquals(s[2], r[0])
        self.assertEquals(2, len(r))
        self.assertEquals([2,3], list(r))

        r = s[0:4:2]
        self.assertEquals([0,2], list(r))
        self.assertEquals(2, r[1])
        r = s[::-1]
        self.assertEquals([5,4,3,2,1,0], list(r))
        self.assertEquals(5, r[0])
        self.assertEquals(0, r[5])
        self.assertEquals(0, r[-1])
        self.assertEquals([5,4], list(r[:2]))
        self.assertEquals(4, r[:4][1])

        self.assertIndexError(s[:2], 4)

    def testWithIntStringPacker(self):
        s = SortedFileList(join(self.tempdir, 'list'), packer=IntStringPacker())
        s.append((0,'string 0'))
        s.append((1,'string 1'))
        self.assertEquals([(0,'string 0'), (1,'string 1')], list(s))

    def testBisectWithIntStringPacker(self):
        s = SortedFileList(join(self.tempdir, 'list'), packer=IntStringPacker())
        for i in range(6):
            s.append((i,'string %s' % i))

        index = bisect_left(s, (3, ''))
        self.assertEquals((3, 'string 3'), s[index])

    def testAppendFailsIfValueMakesListUnsorted(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        s.append(10)
        try:
            s.append(5)
            self.fail()
        except ValueError:
            pass
        self.assertEquals([10], list(s))

    def testAppendSucceedsEvenWhenUnsortedForFileList(self):
        s = FileList(join(self.tempdir, 'list'))
        s.append(10)
        s.append(5)
        self.assertEquals([10,5], list(s))

    def assertIndexError(self, aList, index):
        try:
            aList[index]
            self.fail('IndexError expected')
        except IndexError:
            pass

    def testWithDeletedItems(self):
        def assertListFunctions(aList):
            self.assertEquals(0, aList[0])
            self.assertEquals(2, aList[1])
            self.assertEquals(8, aList[4])
            self.assertEquals(8, aList[-2])
            self.assertEquals(10, aList[-1])

            self.assertEquals([0,2,4,6,8,10], list(aList))
            self.assertEquals([0,2,4,6,8,10], list(aList[-123456:987654]))
            self.assertEquals([0,2,4,6,8,10], list(aList[::-1][::-1]))
            self.assertEquals([10,8,6,4,2,0], list(aList[::-1]))
            self.assertEquals([2,4,6], list(aList[1:4]))
            self.assertTrue(2 in aList)
            self.assertFalse(1 in aList)
            self.assertIndexError(aList, 20)
            self.assertIndexError(aList, -34567)


        s = SortedFileList(join(self.tempdir, 'list1'))
        for i in [0,2,4,6,8,10]:
            s.append(i)
        assertListFunctions(s)
        t = SortedFileList(join(self.tempdir, 'list2'))
        for i in [0,1,2,3,4,5,6,7,8,9,10]:
            t.append(i)
        for i in [1,3,5,7,9]:
            t.remove(i)
        assertListFunctions(t)

    def testDelete(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        for i in range(5):
            s.append(i)
        try:
            s.remove(8)
            self.fail('ValueError expected')
        except ValueError:
            pass
        s.remove(2)
        try:
            s.remove(2)
            self.fail('ValueError expected')
        except ValueError:
            pass
        self.assertEquals(0, s[0])
        self.assertEquals(3, s[2])
        self.assertEquals(4, len(s))

    def testDeleteIsPersistent(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        for i in range(10):
            s.append(i)
        s.remove(2)
        s.remove(6)
        s.remove(4)
        self.assertEquals([0,1,3,5,7,8,9], list(s))
        t = SortedFileList(join(self.tempdir, 'list'))
        self.assertEquals([0,1,3,5,7,8,9], list(t))
        t.remove(7)
        self.assertEquals([0,1,3,5,8,9], list(t))

    def testIndex(self):
        s = SortedFileList(join(self.tempdir, 'list'), mergeTrigger=10)
        for i in range(4):
            s.append(i)
        self.assertEquals(0, s.index(0))


    def testMergeWhenNecessary(self):
        s = SortedFileList(join(self.tempdir, 'list'), mergeTrigger=10)
        for i in range(20):
            s.append(i)
        for i in range(9):
            s.remove(i)
        self.assertEquals(9, len(FileList(join(self.tempdir, 'list.deleted'))))
        s.remove(12)
        self.assertEquals(0, len(FileList(join(self.tempdir, 'list.deleted'))))

    def testDeleteResultingInEmptyListWithMerging(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        s.append(1234)
        s.remove(1234)
        self.assertEquals([], list(s))
        s._merge()
        s._merge()
        self.assertEquals([], list(s))

    def testDeleteResultingInEmptyListWithMerging2(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        s.append(1234)
        s.remove(1234)
        s.append(1235)
        self.assertEquals([1235], list(s))
        s._merge()
        self.assertEquals([1235], list(s))

    def xtestPerformance(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        t0 = time()
        for i in xrange(10**6):
            s.append(i)
            if i%100 == 99:
                s.remove(i-1)
            if i%1000 == 0:
                print i, len(s)
        t1 = time()
        print t1 - t0
        # Appends only, 10**6 within 220 seconds (4500/s)
        # Appends and deletes 1/100, 10**6 within 2754 seconds (363/s)  mergeTrigger=100
