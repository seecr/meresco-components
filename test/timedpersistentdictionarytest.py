## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012, 2016, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2016 SURFmarket https://surf.nl
# Copyright (C) 2016, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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
from seecr.test.io import stderr_replaced

from meresco.components import TimedPersistentDictionary

from time import time
from os.path import join, isfile
from pylru import lrucache


class TimedPersistentDictionaryTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self._filename = join(self.tempdir, "TheDict")
        self.timedDict = TimedPersistentDictionary(TWO_HOURS, filename=self._filename)

    def testPersistent(self):
        self.assertFalse(isfile(self._filename))
        self.timedDict['key'] = 'value'
        self.assertTrue(isfile(self._filename))
        self.assertEqual(dict, type(self.timedDict._dictionary))

        timedDict2 = TimedPersistentDictionary(TWO_HOURS, filename=self._filename)
        self.assertEqual('value', timedDict2['key'])
        self.assertEqual(dict, type(timedDict2._dictionary))

        self.assertEqual(self.timedDict.id(), timedDict2.id())

    def testPersistentPop(self):
        self.timedDict['key'] = "value"
        self.timedDict.pop("key")
        self.assertFalse("key" in self.timedDict)
        timedDict2 = TimedPersistentDictionary(TWO_HOURS, filename=self._filename)
        self.assertFalse("key" in timedDict2)

    def testPersistentClear(self):
        self.timedDict['key'] = 'another value'
        self.assertTrue("key" in self.timedDict)
        self.timedDict.clear()
        self.assertFalse("key" in self.timedDict)
        timedDict2 = TimedPersistentDictionary(TWO_HOURS, filename=self._filename)
        self.assertFalse("key" in timedDict2)

    def testPersistentPurge(self):
        self.timedDict['key'] = "yet another value"
        self.timedDict._now = lambda : time() + TWO_HOURS + TWO_HOURS
        self.assertEqual("yet another value", self.timedDict.peek("key"))
        self.timedDict.purge()
        self.assertFalse("key" in self.timedDict)

        timedDict2 = TimedPersistentDictionary(TWO_HOURS, filename=self._filename)
        self.assertFalse("key" in timedDict2)

    def testPersistentGetExpired(self):
        self.timedDict['key'] = "yet another value"
        self.timedDict._now = lambda : time() + TWO_HOURS + TWO_HOURS
        self.assertEqual(None, self.timedDict.get("key"))
        self.assertFalse("key" in self.timedDict)

        timedDict2 = TimedPersistentDictionary(TWO_HOURS, filename=self._filename)
        self.assertFalse("key" in timedDict2)

    def testPersistentDel(self):
        self.timedDict['key'] = "yet another value"
        self.assertTrue("key" in self.timedDict)

        timedDict2 = TimedPersistentDictionary(TWO_HOURS, filename=self._filename)
        self.assertTrue("key" in timedDict2)

        del timedDict2['key']
        timedDict3 = TimedPersistentDictionary(TWO_HOURS, filename=self._filename)
        self.assertFalse("key" in timedDict3)

    def testPersistentIfLRU(self):
        self.timedDict = TimedPersistentDictionary(TWO_HOURS, filename=self._filename, lruMaxSize=10)
        self.assertFalse(isfile(self._filename))
        self.timedDict['key'] = 'value'
        self.assertTrue(isfile(self._filename))
        self.assertEqual(lrucache, type(self.timedDict._dictionary))

        timedDict2 = TimedPersistentDictionary(TWO_HOURS, filename=self._filename)
        self.assertEqual('value', timedDict2['key'])
        self.assertEqual(lrucache, type(timedDict2._dictionary))

    def testBasicGetAndPut(self):
        self.timedDict['key'] = 'value'
        self.assertEqual('value', self.timedDict['key'])

        self.timedDict['key'] = 'otherValue'
        self.assertEqual('otherValue', self.timedDict['key'])
        self.timedDict['key'] = 5
        self.assertEqual(5, self.timedDict['key'])
        self.timedDict['key'] = 5.0
        self.assertEqual(5.0, self.timedDict['key'])
        self.timedDict['key'] = ['someMutable', 5]
        self.assertEqual(['someMutable', 5], self.timedDict['key'])

        self.assertEqual(['someMutable', 5], self.timedDict.get('key'))

        self.assertRaises(TypeError, self.timedDict.__setitem__, [], 'value')
        self.assertRaises(KeyError, self.timedDict.__getitem__, 'iamnothere')
        self.assertEqual(None, self.timedDict.get('iamnothere'))
        self.assertEqual('MARK', self.timedDict.get('iamnothere', 'MARK'))

    def testBasicContains(self):
        self.timedDict[5] = 'five'
        self.timedDict['six'] = 6
        self.assertTrue(5 in self.timedDict)
        self.assertTrue('six' in self.timedDict)
        self.assertFalse(42 in self.timedDict)
        self.assertFalse(None in self.timedDict)

        self.assertTrue(5 in self.timedDict)
        self.assertTrue('six' in self.timedDict)
        self.assertFalse(42 in self.timedDict)
        self.assertFalse(None in self.timedDict)

    def testBasicDeletion(self):
        self.timedDict['key'] = 'five'

        try:
            del self.timedDict['key']
        except:
            self.fail("This shouldn't happen.")
        self.assertRaises(KeyError, self.timedDict.__delitem__, 'idontexist')

    def testExpirationOrderIsKeptInternally(self):
        self.timedDict[3] = SomeObject(1)
        self.timedDict[1] = SomeObject(10)
        self.timedDict[2] = SomeObject(20)

        self.assertEqual([3, 1, 2], self.timedDict._expirationOrder)

        self.timedDict[1] = SomeObject(23)
        self.assertEqual([3, 2, 1], self.timedDict._expirationOrder)

        self.timedDict[0] = SomeObject(23.01)
        self.assertEqual([3, 2, 1, 0], self.timedDict._expirationOrder)

        del self.timedDict[2]
        self.assertEqual([3, 1, 0], self.timedDict._expirationOrder)

    def testGetTime(self):
        self.timedDict[1] = SomeObject('id1')
        with stderr_replaced():
            self.assertTrue(time() - self.timedDict.getTime(1) < 2.0)

    def testTouch(self):
        self.timedDict[1] = SomeObject('id1')
        self.timedDict[2] = SomeObject('id2')

        self.assertEqual([1, 2], self.timedDict._expirationOrder)
        self.timedDict.touch(1)
        self.assertEqual([2, 1], self.timedDict._expirationOrder)

    def testPurge(self):
        self.timedDict[1] = SomeObject('id1')
        self.timedDict[2] = SomeObject('id2')
        self.timedDict._now = lambda : time() + ONE_HOUR
        self.assertEqual([1, 2], self.timedDict._expirationOrder)

        self.timedDict[3] = SomeObject('id3')
        self.timedDict.touch(2)
        self.timedDict._now = lambda : time() + TWO_HOURS
        self.timedDict.purge()
        self.assertEqual([3, 2], self.timedDict._expirationOrder)
        self.timedDict._now = lambda : time() + TWO_HOURS + TWO_HOURS
        self.timedDict.purge()
        self.assertEqual([], self.timedDict._expirationOrder)

    def testPurgeOnSetItem(self):
        self.timedDict[1] = SomeObject('id1')
        self.timedDict._now = lambda : time() + TWO_HOURS
        self.timedDict[2] = SomeObject('id2')

        self.assertEqual([2], self.timedDict._expirationOrder)

    def testDeleteExpiredOnGetItem(self):
        self.timedDict[1] = SomeObject('id1')
        self.timedDict._now = lambda : time() + TWO_HOURS

        self.assertRaises(KeyError, self.timedDict.__getitem__, 1)
        self.assertEqual([], self.timedDict._expirationOrder)

    def testExpiredOnInShouldReturnDefaultOnGetWithoutAnException(self):
        setTime = time()
        self.timedDict._now = lambda : setTime
        self.timedDict[1] = SomeObject('id1')

        self.timedDict._now = lambda : setTime + TWO_HOURS
        try:
            1 in self.timedDict
        except KeyError:
            self.fail("Key shouldn't have expired yet.")
        except:
            self.fail("This should not happen.")

        self.timedDict._now = lambda : setTime + TWO_HOURS + 0.000001

        self.assertEqual(None, self.timedDict.get(1))
        self.assertEqual('a default', self.timedDict.get(1, 'a default'))
        self.assertEqual([], self.timedDict._expirationOrder)

    def testPop(self):
        setTime = time()
        self.timedDict[1] = "Now you see me, now you don't."
        self.assertEqual("Now you see me, now you don't.", self.timedDict.pop(1))
        self.assertRaises(KeyError, lambda: self.timedDict.pop(1))
        self.assertEqual("default", self.timedDict.pop(1, 'default'))
        self.assertEqual(None, self.timedDict.pop(1, None))
        self.assertEqual("default", self.timedDict.pop(1, default='default'))
        self.assertEqual(None, self.timedDict.pop(1, default=None))
        self.timedDict[1] = "Now you see me, now you don't."
        setTime = time()
        self.timedDict._now = lambda : setTime + TWO_HOURS + 0.000001
        self.assertRaises(KeyError, lambda: self.timedDict.pop(1))

    def testPeek(self):
        self.timedDict[1] = "Now you see me, now you don't."
        self.timedDict._now = lambda : time() + TWO_HOURS

        self.assertEqual("Now you see me, now you don't.", self.timedDict.peek(1))
        self.assertRaises(KeyError, self.timedDict.__getitem__, 1)

    def testClear(self):
        self.timedDict['key'] = 'five'
        self.timedDict.clear()
        self.assertRaises(KeyError, lambda: self.timedDict["key"])

    def testUpdateTimeout(self):
        self.timedDict['key'] = 'five'
        self.timedDict._now = lambda : time() + TWO_HOURS
        self.timedDict.setTimeout(TWO_HOURS + 1)
        self.assertEqual("five", self.timedDict["key"])

    def testSize(self):
        self.assertEqual(0, self.timedDict.size())
        self.timedDict['key'] = 'five'
        self.assertEqual(1, self.timedDict.size())
        self.timedDict['key'] = 'six'
        self.assertEqual(1, self.timedDict.size())
        self.timedDict['key2'] = 'six'
        self.assertEqual(2, self.timedDict.size())
        self.timedDict._now = lambda : time() + TWO_HOURS
        self.assertEqual(0, self.timedDict.size())

    def testLruMaxSize(self):
        timedDict = TimedPersistentDictionary(TWO_HOURS, filename=join(self.tempdir, "TheDict"), lruMaxSize=2)
        self.assertEqual(0, timedDict.size())
        timedDict['key'] = 'five'
        self.assertEqual(1, timedDict.size())
        timedDict['key1'] = 'six'
        self.assertEqual(2, timedDict.size())
        self.assertEqual('five', timedDict['key'])
        timedDict['key2'] = 'seven'
        self.assertEqual(2, timedDict.size())
        self.assertEqual(set(['key', 'key2']), set(timedDict.keys()))

    def testExpiredLeastRecentlyUsedGracefullyDealtWith(self):
        timedDict = TimedPersistentDictionary(TWO_HOURS, filename=join(self.tempdir, "TheDict"), lruMaxSize=2)
        timedDict['key1'] = 'five'
        timedDict['key2'] = 'six'
        timedDict['key3'] = 'seven'
        self.assertEqual(set(['key2', 'key3']), set(timedDict.keys()), set(timedDict.keys()))
        self.assertEqual(3, len(timedDict._times))
        self.assertEqual(3, len(timedDict._expirationOrder))
        timedDict.purge()
        self.assertEqual(2, len(timedDict._times))
        self.assertEqual(2, len(timedDict._expirationOrder))
        timedDict._now = lambda : time() + TWO_HOURS
        timedDict.purge()
        self.assertEqual([], list(timedDict.keys()))
        self.assertEqual(0, len(timedDict._times))
        self.assertEqual(0, len(timedDict._expirationOrder))

    # def testSpeed(self):
    #     timedDict = TimedDictionary(TWO_HOURS)
    #     total = 50000
    #     t0 = time()
    #     for i in xrange(total):
    #         timedDict[i] = i + 1
    #     t1 = time()
    #     print 'Took per set:', ((t1 - t0) / total)


ONE_HOUR = 3600
TWO_HOURS = ONE_HOUR * 2

class SomeObject(object):
    def __init__(self, id):
        self.id = id
