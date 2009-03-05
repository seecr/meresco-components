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
