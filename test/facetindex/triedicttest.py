## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009-2010 Delft University of Technology http://www.tudelft.nl
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

from unittest import TestCase

from meresco.components.facetindex.triedict import TrieDict

class TrieDictTest(TestCase):
    def testConstructor(self):
        t = TrieDict()
        
    def testAddWords(self):
        t = TrieDict(uselocalpool=1)
        termId1 = t.add('xy', 1)
        termId2 = t.add('y', 1)
        self.assertEquals(termId1, t.add('xy', 1))
        self.assertEquals(termId2, t.add('y', 1))

    def testAddWords2(self):
        t = TrieDict(uselocalpool=1)
        termId1 = t.add('xy', 8)
        termId2 = t.add('x', 6)
        self.assertEquals(8, t.getValue('xy'))
        self.assertEquals(6, t.getValue('x'))
        self.assertEquals(termId1, t.add('xy', 1))
        self.assertEquals(termId2, t.add('x', 1))
        
    def testAddWords3(self):
        t = TrieDict(uselocalpool=1)
        termId1 = t.add('x', 1)
        termId2 = t.add('xy', 1)
        
        self.assertEquals(termId1, t.add('x', 1))
        self.assertEquals(termId2, t.add('xy', 1))
        
    def testAddAndGet(self):
        t = TrieDict(uselocalpool=1)
        self.assertEquals(0xffffffff, t.getValue('q'))
        t.add('q', 1)
        self.assertEquals(1, t.getValue('q'))        
