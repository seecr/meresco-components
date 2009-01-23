from unittest import TestCase

from merescocomponents.facetindex import IntegerList

class IntegerListTest(TestCase):

    def testConstruct(self):
        l = IntegerList()
        self.assertEquals(0, len(l))
        l = IntegerList(10)
        self.assertEquals(10, len(l))
        self.assertEquals([0,1,2,3,4,5,6,7,8,9], list(l))

    def testAppend(self):
        l = IntegerList()
        l.append(4)
        self.assertEquals([4], list(l))
        l.append(8)
        self.assertEquals([4,8], list(l))

    def testLen(self):
        l = IntegerList()
        self.assertEquals(0, len(l))

        l.append(1)
        self.assertEquals(1, len(l))

    def testIndex(self):
        l = IntegerList(100)

        self.assertEquals(0, l[0])
        self.assertEquals(66, l[66])
        self.assertEquals(99, l[-1])
        self.assertEquals(98, l[-2])
        self.assertEquals(90, l[-10])

    def testSlicing(self):
        l = IntegerList(100)
        self.assertEquals([0,1], l[:2])
        self.assertEquals([1,2,3,4], l[1:5])
        self.assertEquals([98, 99], l[98:])
        self.assertEquals([98, 99], l[-2:])

    def testCopySlice(self):
        l = IntegerList(100)
        m = l[:]
        self.assertEquals(100, len(m))

    def testExtend(self):
        l = IntegerList()
        l.extend([1,2])
        self.assertEquals(2, len(l))
        self.assertEquals([1,2], list(l))

        l.extend([3,4])
        self.assertEquals(4, len(l))
        self.assertEquals([1,2,3,4], list(l))

    def testDel(self):
        l = IntegerList()
        l.extend([1,2])
        del l[0]
        self.assertEquals(1, len(l))
        self.assertEquals([2], list(l))

    def testDelSlice(self):
        l = IntegerList(10)
        del l[5:]
        self.assertEquals([0,1,2,3,4], list(l))

    def testEquality(self):
        l1 = IntegerList(10)
        l2 = IntegerList(10)
        self.assertEquals(l1, l2)

    def testCopy(self):
        l = IntegerList(5)
        copy = l.copy()
        self.assertEquals([0,1,2,3,4], list(l))
        self.assertEquals(5, len(copy))
        self.assertEquals([0,1,2,3,4], list(copy))
        l.append(9)
        copy.append(7)
        self.assertEquals([0,1,2,3,4, 9], list(l))
        self.assertEquals([0,1,2,3,4, 7], list(copy))

    def testSetItem(self):
        l = IntegerList(5)
        l[0] = 10
        self.assertEquals([10,1,2,3,4], list(l))

        l = IntegerList(5)
        l[2] = -1
        self.assertEquals([0,1,-1,3,4], list(l))

    def testDitchHolesStartingAt(self):
        l = IntegerList(5)
        l.mergeFromOffset(0)
        self.assertEquals([0,1,2,3,4], list(l))

        l = IntegerList(5)
        l[2] = -1
        l[4] = -1
        l.mergeFromOffset(0)
        self.assertEquals([0,1,3], list(l))

        l = IntegerList(5)
        l[2] = -1
        l[4] = -1
        l.mergeFromOffset(3)
        self.assertEquals([0,1,-1,3], list(l))

        l = IntegerList(5)
        for i in range(5):
            l[i] = -1
        l.mergeFromOffset(0)
        self.assertEquals([], list(l))

        l = IntegerList(5)
        l[2] = -1
        l.mergeFromOffset(2)
        self.assertEquals([0, 1, 3, 4], list(l))
