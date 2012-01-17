# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 Kennisnet http://www.kennisnet.nl
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.components import DoubleUniqueBerkeleyDict, BerkeleyDict

class BerkeleyDictTestBase(SeecrTestCase):
    def testInsert(self):
        self.bdict['1'] = 'some string'
        self.assertEquals('some string', self.bdict['1'])
        self.bdict['1'] = 'some other string'
        self.assertEquals('some other string', self.bdict['1'])

    def testNoneExistingKey(self):
        try:
            self.bdict['not']
            self.fail()
        except KeyError:
            pass

    def testDelete(self):
        self.bdict['1'] = 'a string'
        self.assertEquals('a string', self.bdict['1'])
        del self.bdict['1']
        try:
            self.bdict['1']
            self.fail('must not come here')
        except KeyError:
            pass

    def testGet(self):
        self.bdict['1'] = 'some other string'

        self.assertEquals('some other string', self.bdict.get('1', 'something'))
        self.assertEquals('something', self.bdict.get('2', 'something'))

    def testStopWord(self):
        self.bdict['the'] = 'an'
        self.assertEquals('an', self.bdict['the'])

    def testCase(self):
        self.bdict['The'] = 'De'
        self.bdict['the'] = 'de'
        self.assertEquals('De', self.bdict['The'])
        self.assertEquals('de', self.bdict['the'])

    def testSpaces(self):
        self.bdict['The one'] = 'De ene'
        self.assertEquals('De ene', self.bdict['The one'])
        
class DoubleUniqueBerkeleyDictTest(BerkeleyDictTestBase):
    def setUp(self):
        BerkeleyDictTestBase.setUp(self)
        self.bdict = DoubleUniqueBerkeleyDict(self.tempdir)

    def testDelete(self):
        BerkeleyDictTestBase.testDelete(self)
        self.assertEquals(None, self.bdict.getKeyFor('a string'))

    def testGetKeyFor(self):
        self.bdict['1'] = 'one'
        self.bdict['2'] = 'two'
        self.assertEquals('1', self.bdict.getKeyFor('one'))

class BerkeleyDictTest(BerkeleyDictTestBase):
    def setUp(self):
        BerkeleyDictTestBase.setUp(self)
        self.bdict = BerkeleyDict(self.tempdir)
