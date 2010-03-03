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
from unittest import TestCase
from merescocomponents.facetindex import Trie
from time import time

class TrieTest(TestCase):

    def testCreate(self):
        trie = Trie()
        self.assertTrue(trie != None)

    def testLargeValue(self):
        trie = Trie()
        trie.add(123456789, 'a')

    def testTrieWithOneValue(self):
        trie = Trie()
        trie.add(0, 'x')
        self.assertEquals(0, trie.getValue('x'))

    def testGetValueForDistinctTerms(self):
        trie = Trie()
        trie.add(7, 'one')
        self.assertEquals(7, trie.getValue('one'))
        trie.add(2, 'two')
        trie.add(4, 'four')
        self.assertEquals(2, trie.getValue('two'))
        self.assertEquals(4, trie.getValue('four'))

    def testGetValueForTermsWithSharedPrefixes(self):
        trie = Trie()
        self.assertEquals("default", trie.getValue('term0', "default"))
        trie.add(0, "term0")
        self.assertEquals(0, trie.getValue('term0'))
        self.assertEquals("default", trie.getValue('te', "default"))

    def testConvertLeafToNodeWithChildren(self):
        trie = Trie()
        trie.add(8,'a')
        self.assertEquals(8, trie.getValue('a'))
        trie.add(3,'ab')
        self.assertEquals(8, trie.getValue('a'))
        self.assertEquals(3, trie.getValue('ab'))
        trie.add(4,'az')
        trie.add(6,'bz')

    def testNewNodeInMiddleOfTree(self):
        trie = Trie()
        trie.add(0, "middle of tree")
        trie.add(1, "middle")
        self.assertEquals(0, trie.getValue("middle of tree"))
        self.assertEquals(1, trie.getValue("middle"))

    def testPrefixNotAccidentallyFound(self):
        trie = Trie()
        trie.add(0, "prefix")
        self.assertEquals("default", trie.getValue("prefix, but other stuff follows", "default"))

    def testGetValuesEmptyTrie(self):
        trie = Trie()
        self.assertEquals([], trie.getValues(""))
        self.assertEquals([], trie.getValues("abc"))

    def testGetValuesTrieWithOneCharacter(self):
        trie = Trie()
        trie.add(0, "X")
        self.assertEquals([0], trie.getValues(""))
        self.assertEquals([], trie.getValues("abc"))
        self.assertEquals([0], trie.getValues("X"))
        self.assertEquals([], trie.getValues("Xyz"))

    def testGetValuesTrieWithString(self):
        trie = Trie()
        trie.add(0, "abcd")
        self.assertEquals([0], trie.getValues(""))
        self.assertEquals([], trie.getValues("xxx"))
        self.assertEquals([0], trie.getValues("abc"))
        self.assertEquals([0], trie.getValues("abcd"))
        self.assertEquals([], trie.getValues("abcde"))

    def testGetValuesTrieWithList(self):
        trie = Trie()
        trie.add(0, "abcd")
        trie.add(1, "a000")
        self.assertEquals([1, 0], trie.getValues(""))
        self.assertEquals([1, 0], trie.getValues("a"))
        self.assertEquals([], trie.getValues("xxx"))
        self.assertEquals([0], trie.getValues("abc"))
        self.assertEquals([0], trie.getValues("abcd"))
        self.assertEquals([], trie.getValues("abcde"))
        self.assertEquals([1], trie.getValues("a00"))
        self.assertEquals([1], trie.getValues("a000"))
        self.assertEquals([], trie.getValues("a0000"))

    def testGetValues(self):
        trie = Trie()
        trie.add(0, "prefix-0")
        trie.add(1, "prefix-1")
        trie.add(2, "prefix-2")
        trie.add(3, "prefix-3")
        trie.add(4, "z0-iets anders")
        trie.add(5, "z1-meer")
        trie.add(6, "z2-spul")
        trie.add(7, "z3-enzo")
        self.assertEquals(range(8), trie.getValues(""))
        self.assertEquals(range(4), trie.getValues("prefix"))
        self.assertEquals([0], trie.getValues("prefix-0"))
        self.assertEquals([1], trie.getValues("prefix-1"))
        self.assertEquals([], trie.getValues("prefix-0-enmeer"))
        self.assertEquals([], trie.getValues("not found"))

    def testSearchBugWithCaseSensitivityOnNumbers(self):
        trie = Trie()
        trie.add(0, "prefix-0")
        trie.add(1, "prefix-1")
        self.assertEquals([0], trie.getValues("prefix-0"))

    def testCaseInsensitive(self):
        trie = Trie()
        trie.add(0, 'A')
        trie.add(1, 'a')

        def trieGetValues(aString):
            return sorted(trie.getValues(aString))

        self.assertEquals([0, 1], trieGetValues(''))
        self.assertEquals([0, 1], trieGetValues('a'))
        self.assertEquals([0, 1], trieGetValues('A'))
        self.assertEquals([], trieGetValues('a0'))
        self.assertEquals([], trieGetValues('A0'))


    def testSomeComplicatedCases(self):
        trie = Trie()
        trie.add(0,'ABC')
        trie.add(1,'abc')
        trie.add(2,'aBc')
        trie.add(3,'aB stuff')
        trie.add(4,'Ab')
        trie.add(5,'iets anders')
        trie.add(6, 'met spAtIE')
        trie.add(7, 'met xxx creates stringnode')

        def trieGetValues(aString):
            return sorted(trie.getValues(aString))

        self.assertEquals(range(8), trieGetValues(''))
        self.assertEquals(range(5), trieGetValues('ab'))
        self.assertEquals(range(5), trieGetValues('AB'))
        self.assertEquals(range(3), trieGetValues('aBc'))
        self.assertEquals([], trieGetValues('aBc---'))
        self.assertEquals([6, 7], trieGetValues('met '))

    def testList(self):
        trie = Trie()
        trie.add(0,'a') # creates trieNode + one leafNode
        self.assertEquals(0, trie.getValue('a'))
        trie.add(1,'aa') # turns leafNode into listNode and add 'a'
        self.assertEquals(1, trie.getValue('aa'))
        trie.add(2,'aaa') # adds one string 'aa' to listNode
        self.assertEquals(2, trie.getValue('aaa'))
        trie.add(3,'aaaa') # adds one string 'aaa' to listNode
        self.assertEquals(3, trie.getValue('aaaa'))
        trie.add(4,'aaaaa') # bursts listNode into trieNode
        self.assertEquals(4, trie.getValue('aaaaa'))
        self.assertEquals(3, trie.getValue('aaaa'))
        self.assertEquals(2, trie.getValue('aaa'))
        self.assertEquals(1, trie.getValue('aa'))
        self.assertEquals(0, trie.getValue('a'))
        trie.add(5,'ab') # adds one leafNode to trieNode
        self.assertEquals(5, trie.getValue('ab'))
        trie.add(6,'ac') # adds one leafNode to trieNode
        self.assertEquals(6, trie.getValue('ac'))
        trie.add(7,'aaaaaaaa')
        self.assertEquals(7, trie.getValue('aaaaaaaa'))
        self.assertEquals(4, trie.getValue('aaaaa'))
        self.assertEquals(3, trie.getValue('aaaa'))
        self.assertEquals(2, trie.getValue('aaa'))
        self.assertEquals(1, trie.getValue('aa'))
        self.assertEquals(0, trie.getValue('a'))
        
    def testOneCharacter(self):
        trie = Trie()
        trie.add(42, 'aa')
        trie.add(87, 'a')
        self.assertEquals(87, trie.getValue('a'))
