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
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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
from os import rename, remove, listdir
from os.path import join, isfile
from bisect import bisect_left, bisect_right
from random import choice

from meresco.components import PersistentSortedIntegerList
from meresco.components.facetindex import IntegerList
from time import time


class FullStopException(Exception): pass

class PersistentSortedIntegerListTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.filepath = join(self.tempdir, 'list')

    def testAppendAndWrite(self):
        s = PersistentSortedIntegerList(self.filepath, use64bits=True)
        s.append(1)
        s.append(2)
        self.assertEquals([1,2], list(iter(s)))
        self.assertEquals(16, len(open(self.filepath).read()))
        self.assertEquals([1,2], list(s))
        s = PersistentSortedIntegerList(self.filepath, use64bits=True)
        self.assertEquals([1,2], list(iter(s)))
        self.assertEquals(len(s), len(list(s)))

    def testEmpty(self):
        s = PersistentSortedIntegerList(self.filepath, use64bits=True)
        self.assertEquals([], list(s))

    def testContains(self):
        s = PersistentSortedIntegerList(self.filepath, use64bits=True)
        for i in range(0,20,2):
            s.append(i)
        self.assertTrue(14 in s)
        self.assertFalse(15 in s)
        self.assertFalse(32 in s)

    def testZero(self):
        s = PersistentSortedIntegerList(self.filepath, use64bits=True)
        s.append(0)
        self.assertEquals([0], list(s))

    def testGetItem(self):
        s = PersistentSortedIntegerList(self.filepath, use64bits=True)
        for i in range(20):
            s.append(i)
        self.assertEquals(2, s[2])
        self.assertRaises(IndexError, lambda: s[1234567])
        self.assertEquals(19, s[-1])
        self.assertEquals(0, s[-20])
        self.assertRaises(IndexError, lambda: s[-21])

    def testSlicing(self):
        s = PersistentSortedIntegerList(self.filepath, use64bits=True)
        for i in range(6):
            s.append(i)
        self.assertEquals([], list(s[0:0]))
        self.assertEquals([1,2], list(s[1:3]))
        self.assertEquals([0,1,2,3], list(s[:-2]))
        self.assertEquals([4,5], list(s[-2:]))
        self.assertRaises(ValueError, lambda: s[:4:2])
        self.assertRaises(ValueError, lambda: s[::-1])
        self.assertEquals([], list(s[4:3]))
        self.assertEquals([0,1,2,3,4,5], list(s[-12345:234567]))
        self.assertEquals([1,2], list(s[1:3]))

    def testAppendFailsIfValueMakesListUnsorted(self):
        s = PersistentSortedIntegerList(self.filepath, use64bits=True)
        s.append(10)
        try:
            s.append(5)
            self.fail()
        except ValueError, e:
            self.assertEquals('list.append(5): expected value to be greater than 10', str(e))
        try:
            s.append(10)
            self.fail()
        except ValueError, e:
            self.assertEquals('list.append(10): expected value to be greater than 10', str(e))
        self.assertEquals([10], list(s))
        
    def testWithDeletedItems(self):
        def assertListFunctions(aList):
            self.assertEquals(0, aList[0])
            self.assertEquals(2, aList[1])
            self.assertEquals(8, aList[4])
            self.assertEquals(8, aList[-2])
            self.assertEquals(10, aList[-1])
            
            self.assertEquals([0,2,4,6,8,10], list(aList))
            self.assertEquals([0,2,4,6,8,10], list(aList[-123456:987654]))
            self.assertEquals([2,4,6], list(aList[1:4]))
            self.assertTrue(2 in aList)
            self.assertFalse(1 in aList)
            self.assertRaises(IndexError, lambda: aList[20])
            self.assertRaises(IndexError, lambda: aList[-34567])
            
        s = PersistentSortedIntegerList(join(self.tempdir, 'list1'))
        for i in [0,2,4,6,8,10]:
            s.append(i)
        assertListFunctions(s)
        t = PersistentSortedIntegerList(join(self.tempdir, 'list2'))
        for i in [0,1,2,3,4,5,6,7,8,9,10]:
            t.append(i)
        for i in [1,3,5,7,9]:
            t.remove(i)
        assertListFunctions(t)

    def testDelete(self):
        s = PersistentSortedIntegerList(self.filepath, use64bits=True)
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
        s = PersistentSortedIntegerList(self.filepath, use64bits=True)
        for i in range(10):
            s.append(i)
        s.remove(2)
        s.remove(6)
        s.remove(4)
        self.assertEquals([0,1,3,5,7,8,9], list(s))
        t = PersistentSortedIntegerList(self.filepath, use64bits=True)
        self.assertEquals([0,1,3,5,7,8,9], list(t))
        t.remove(7)
        t = PersistentSortedIntegerList(self.filepath, use64bits=True)
        self.assertEquals([0,1,3,5,8,9], list(t))

    def testIndex(self):
        s = PersistentSortedIntegerList(self.filepath, use64bits=True)
        for i in range(4):
            s.append(i)
        self.assertEquals(0, s.index(0))
        self.assertEquals(3, s.index(3))
       
    def testRecoverFromCrash(self):
        mergeSteps = [0]
        recoverSteps = [0]
        crashSave = [False]

        def crashingRename(fromPath, toPath):
            rename(fromPath, toPath)
            mergeSteps[0] += 1
            if mergeSteps[0] == mergeCrashTrigger:
                raise FullStopException("forced crash after %d merge steps (renaming %s to %s)" % (mergeSteps[0], fromPath, toPath))

        def crashingRemove(filepath):
            remove(filepath)
            mergeSteps[0] += 1
            if mergeSteps[0] == mergeCrashTrigger:
                raise FullStopException("forced crash after %d merge steps (removing %s)" % (mergeSteps[0], filepath))

        def crashingSave(list, filepath, offset, append):
            list.save(filepath, offset=offset, append=append)
            if crashSave[0] and crashSave[0](filepath):
                mergeSteps[0] += 1
                if mergeSteps[0] == mergeCrashTrigger:
                    raise FullStopException("forced crash after %d merge steps (saving %s)" % (mergeSteps[0], filepath))

        class MockPersistentSortedIntegerList(PersistentSortedIntegerList):
            def _remove(self, filepath):
                remove(filepath)
                recoverSteps[0] += 1
                if recoverSteps[0] == recoverCrashTrigger:
                    raise FullStopException("forced crash after %d recover steps (removing %s)" % (recoverSteps[0], filepath))

            def _rename(self, fromPath, toPath):
                rename(fromPath, toPath)
                recoverSteps[0] += 1
                if recoverSteps[0] == recoverCrashTrigger:
                    raise FullStopException("forced crash after %d recover steps (renaming %s to %s)" % (recoverSteps[0], fromPath, toPath))
            def _save(self, list, filepath, offset, append):
                list.save(filepath, offset=offset, append=append)
                recoverSteps[0] += 1
                if recoverSteps[0] == recoverCrashTrigger:
                    raise FullStopException("forced crash after %d recover steps (saving %s)" % (mergeSteps[0], filepath))

        def mergeCrashRecover():
            mergeSteps[0] = 0
            recoverSteps[0] = 0
            crashSave[0] = False
            if isfile(self.filepath):
                remove(self.filepath)
            s = PersistentSortedIntegerList(self.filepath, use64bits=True, mergeTrigger=2)
            s._rename = crashingRename
            s._remove = crashingRemove
            s._save = crashingSave
            try:
                for i in range(4):
                    s.append(i)
                for i in range(2):
                    if i == 1:
                        crashSave[0] = lambda filepath: not filepath.endswith('.deleted')
                    s.remove(i)
            except FullStopException, e:
                pass
            try:
                s = MockPersistentSortedIntegerList(self.filepath, use64bits=True)
            except FullStopException, e:
                pass
            s = PersistentSortedIntegerList(self.filepath, use64bits=True)
            return s

        for mergeCrashTrigger in xrange(1, 20):
            for recoverCrashTrigger in xrange(1, 20):
                s = mergeCrashRecover()
                self.assertEquals([2,3], list(s))            
                self.assertTrue(isfile(self.filepath))
                self.assertFalse(isfile(self.filepath + '.deleted'))
                self.assertFalse(isfile(self.filepath + '.new'))
                self.assertFalse(isfile(self.filepath + '.current'))
                self.assertFalse(isfile(self.filepath + '.deleted.current'))

    def testPerformance(self):
        mergeTrigger = 100
        size = 10**6
        measurements = 1000

        t = time()
        s = PersistentSortedIntegerList(self.filepath, use64bits=True, mergeTrigger=mergeTrigger)
        s._iList = IntegerList(size, use64bits=True)
        s._iList.save(self.filepath, offset=0, append=False)
        tCreate = time() - t

        tIn = 0
        tAppend = 0
        tDelete = 0
        for i in xrange(measurements):
            t = time()
            size in s
            tIn += time() - t

            t = time()
            s.append(size + i)
            tAppend += time() - t

            element = choice(s)
            t = time()
            s.remove(element)
            tDelete += time() - t

        self.assertTiming(0.0, tCreate, 0.050)
        self.assertTiming(0.0, tIn / measurements, 0.001)
        self.assertTiming(0.0, tAppend / measurements, 0.001)
        self.assertTiming(0.0, tDelete / measurements, 0.003)

