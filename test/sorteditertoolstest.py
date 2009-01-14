from unittest import TestCase, main

from merescocomponents.sorteditertools import PeekIterator, OrIterator, AndIterator

class SortedItertoolsTest(TestCase):
    def testOne(self):
        p = PeekIterator([0,1])
        self.assertEquals(0, p.peek())
        self.assertEquals(0, p.next())
        self.assertEquals(1, p.next())

    def assertOr(self, result, left, right):
        self.assertEquals(result, list(OrIterator(left, right)))

    def testOr(self):
        self.assertOr([1,2,3,4], [1,2,3], [2,3,4])
        self.assertOr([1,2,3,4], [1,2], [3,4])
        self.assertOr([1,2,3,4], [3,4], [1,2])
        self.assertOr([1,2,3,4], [], [1,2,3,4])
        self.assertOr([1,2,3,4], [3], [1,2,3,4])

    def assertAnd(self, result, left, right):
        self.assertEquals(result, list(AndIterator(left, right)))

    def testAnd(self):
        self.assertAnd([2,3], [1,2,3], [2,3,4])
        self.assertAnd([], [1,2], [3,4])
        self.assertAnd([], [3,4], [1,2])
        self.assertAnd([], [], [1,2,3,4])
        self.assertAnd([3], [3], [1,2,3,4])
        self.assertAnd([10],[1,3,5,7,9,10], [2,4,6,8,10])
        self.assertAnd([],[1,3,5,7,9], [2,4,6,8,10])

    def testCombineALotOfIteratorsWithReduce(self):
        myIter = reduce(OrIterator, [[1,2,3],[5,6,7],[2,6,8],[4,6,9,10]])
        self.assertEquals([1,2,3,4,5,6,7,8,9,10],list(myIter))
        myIter = reduce(OrIterator, [[1,2,3]])
        self.assertEquals([1,2,3],list(myIter))
