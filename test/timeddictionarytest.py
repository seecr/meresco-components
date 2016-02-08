## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012, 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2016 Stichting Kennisnet http://www.kennisnet.nl
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

from time import sleep

from unittest import TestCase
from seecr.test.io import stderr_replaced

from meresco.components import TimedDictionary

from time import time


class TimedDictionaryTest(TestCase):
    def testBasicGetAndPut(self):
        timedDict = TimedDictionary(TWO_HOURS)
        timedDict['key'] = 'value'
        self.assertEquals('value', timedDict['key'])

        timedDict['key'] = 'otherValue'
        self.assertEquals('otherValue', timedDict['key'])
        timedDict['key'] = 5
        self.assertEquals(5, timedDict['key'])
        timedDict['key'] = 5.0
        self.assertEquals(5.0, timedDict['key'])
        timedDict['key'] = ['someMutable', 5]
        self.assertEquals(['someMutable', 5], timedDict['key'])

        self.assertEquals(['someMutable', 5], timedDict.get('key'))

        self.assertRaises(TypeError, timedDict.__setitem__, [], 'value')
        self.assertRaises(KeyError, timedDict.__getitem__, 'iamnothere')
        self.assertEquals(None, timedDict.get('iamnothere'))
        self.assertEquals('MARK', timedDict.get('iamnothere', 'MARK'))

    def testBasicContains(self):
        timedDict = TimedDictionary(TWO_HOURS)
        timedDict[5] = 'five'
        timedDict['six'] = 6
        self.assertTrue(5 in timedDict)
        self.assertTrue('six' in timedDict)
        self.assertFalse(42 in timedDict)
        self.assertFalse(None in timedDict)

        self.assertTrue(timedDict.has_key(5))
        self.assertTrue(timedDict.has_key('six'))
        self.assertFalse(timedDict.has_key(42))
        self.assertFalse(timedDict.has_key(None))

    def testBasicDeletion(self):
        timedDict = TimedDictionary(TWO_HOURS)
        timedDict['key'] = 'five'

        try:
            del timedDict['key']
        except:
            self.fail("This shouldn't happen.")
        self.assertRaises(KeyError, timedDict.__delitem__, 'idontexist')

    def testExpirationOrderIsKeptInternally(self):
        timedDict = TimedDictionary(TWO_HOURS)
        timedDict[3] = SomeObject(1)
        timedDict[1] = SomeObject(10)
        timedDict[2] = SomeObject(20)

        self.assertEquals([3, 1, 2], timedDict._expirationOrder)

        timedDict[1] = SomeObject(23)
        self.assertEquals([3, 2, 1], timedDict._expirationOrder)

        timedDict[0] = SomeObject(23.01)
        self.assertEquals([3, 2, 1, 0], timedDict._expirationOrder)

        del timedDict[2]
        self.assertEquals([3, 1, 0], timedDict._expirationOrder)

    def testGetTime(self):
        timedDict = TimedDictionary(TWO_HOURS)
        timedDict[1] = SomeObject('id1')
        with stderr_replaced():
            self.assertTrue(time() - timedDict.getTime(1) < 2.0)

    def testTouch(self):
        timedDict = TimedDictionary(TWO_HOURS)
        timedDict[1] = SomeObject('id1')
        timedDict[2] = SomeObject('id2')

        self.assertEquals([1, 2], timedDict._expirationOrder)
        timedDict.touch(1)
        self.assertEquals([2, 1], timedDict._expirationOrder)

    def testPurge(self):
        timedDict = TimedDictionary(TWO_HOURS)
        timedDict[1] = SomeObject('id1')
        timedDict[2] = SomeObject('id2')
        timedDict._now = lambda : time() + ONE_HOUR
        self.assertEquals([1, 2], timedDict._expirationOrder)

        timedDict[3] = SomeObject('id3')
        timedDict.touch(2)
        timedDict._now = lambda : time() + TWO_HOURS
        timedDict.purge()
        self.assertEquals([3, 2], timedDict._expirationOrder)
        timedDict._now = lambda : time() + TWO_HOURS + TWO_HOURS
        timedDict.purge()
        self.assertEquals([], timedDict._expirationOrder)

    def testPurgeOnSetItem(self):
        timedDict = TimedDictionary(TWO_HOURS)
        timedDict[1] = SomeObject('id1')
        timedDict._now = lambda : time() + TWO_HOURS
        timedDict[2] = SomeObject('id2')

        self.assertEquals([2], timedDict._expirationOrder)

    def testDeleteExpiredOnGetItem(self):
        timedDict = TimedDictionary(TWO_HOURS)
        timedDict[1] = SomeObject('id1')
        timedDict._now = lambda : time() + TWO_HOURS

        self.assertRaises(KeyError, timedDict.__getitem__, 1)
        self.assertEquals([], timedDict._expirationOrder)

    def testExpiredOnInShouldReturnDefaultOnGetWithoutAnException(self):
        timedDict = TimedDictionary(TWO_HOURS)
        setTime = time()
        timedDict._now = lambda : setTime
        timedDict[1] = SomeObject('id1')

        timedDict._now = lambda : setTime + TWO_HOURS
        try:
            1 in timedDict
        except KeyError:
            self.fail("Key shouldn't have expired yet.")
        except:
            self.fail("This should not happen.")

        timedDict._now = lambda : setTime + TWO_HOURS + 0.000001

        self.assertEquals(None, timedDict.get(1))
        self.assertEquals('a default', timedDict.get(1, 'a default'))
        self.assertEquals([], timedDict._expirationOrder)

    def testPeek(self):
        timedDict = TimedDictionary(TWO_HOURS)
        timedDict[1] = "Now you see me, now you don't."
        timedDict._now = lambda : time() + TWO_HOURS

        self.assertEquals("Now you see me, now you don't.", timedDict.peek(1))
        self.assertRaises(KeyError, timedDict.__getitem__, 1)

    def testClear(self):
        timedDict = TimedDictionary(TWO_HOURS)
        timedDict['key'] = 'five'
        timedDict.clear()
        self.assertRaises(KeyError, lambda: timedDict["key"])

    def testUpdateTimeout(self):
        timedDict = TimedDictionary(TWO_HOURS)
        timedDict['key'] = 'five'
        timedDict._now = lambda : time() + TWO_HOURS
        timedDict.setTimeout(TWO_HOURS + 1)
        self.assertEquals("five", timedDict["key"])

    def testSize(self):
        timedDict = TimedDictionary(TWO_HOURS)
        self.assertEqual(0, timedDict.size())
        timedDict['key'] = 'five'
        self.assertEqual(1, timedDict.size())
        timedDict['key'] = 'six'
        self.assertEqual(1, timedDict.size())
        timedDict['key2'] = 'six'
        self.assertEqual(2, timedDict.size())
        timedDict._now = lambda : time() + TWO_HOURS
        self.assertEqual(0, timedDict.size())

    def testLruMaxSize(self):
        timedDict = TimedDictionary(TWO_HOURS, lruMaxSize=2)
        self.assertEqual(0, timedDict.size())
        timedDict['key'] = 'five'
        self.assertEqual(1, timedDict.size())
        timedDict['key1'] = 'six'
        self.assertEqual(2, timedDict.size())
        self.assertEquals('five', timedDict['key'])
        timedDict['key2'] = 'seven'
        self.assertEqual(2, timedDict.size())
        self.assertEquals(set(['key', 'key2']), set(timedDict.keys()))

    def testExpiredLeastRecentlyUsedGracefullyDealtWith(self):
        timedDict = TimedDictionary(TWO_HOURS, lruMaxSize=2)
        timedDict['key1'] = 'five'
        timedDict['key2'] = 'six'
        timedDict['key3'] = 'seven'
        self.assertEquals(set(['key2', 'key3']), set(timedDict.keys()), set(timedDict.keys()))
        self.assertEquals(3, len(timedDict._times))
        self.assertEquals(3, len(timedDict._expirationOrder))
        timedDict.purge()
        self.assertEquals(2, len(timedDict._times))
        self.assertEquals(2, len(timedDict._expirationOrder))
        timedDict._now = lambda : time() + TWO_HOURS
        timedDict.purge()
        self.assertEquals([], list(timedDict.keys()))
        self.assertEquals(0, len(timedDict._times))
        self.assertEquals(0, len(timedDict._expirationOrder))

ONE_HOUR = 3600
TWO_HOURS = ONE_HOUR * 2

class SomeObject(object):
    def __init__(self, id):
        self.id = id
