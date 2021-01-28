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
# Copyright (C) 2012, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 Stichting Kennisnet https://www.kennisnet.nl
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

from meresco.components import DoubleUniqueBerkeleyDict, BerkeleyDict

class BerkeleyDictTestBase(SeecrTestCase):
    def testInsert(self):
        self.bdict[b'1'] = b'some string'
        self.assertEqual(b'some string', self.bdict[b'1'])
        self.bdict[b'1'] = b'some other string'
        self.assertEqual(b'some other string', self.bdict[b'1'])

    def testNoneExistingKey(self):
        try:
            self.bdict[b'not']
            self.fail()
        except KeyError:
            pass

    def testDelete(self):
        self.bdict[b'1'] = b'a string'
        self.assertEqual(b'a string', self.bdict[b'1'])
        del self.bdict[b'1']
        try:
            self.bdict[b'1']
            self.fail('must not come here')
        except KeyError:
            pass

    def testGet(self):
        self.bdict[b'1'] = b'some other string'

        self.assertEqual(b'some other string', self.bdict.get(b'1', 'something'))
        self.assertEqual('something', self.bdict.get(b'2', 'something'))

    def testStopWord(self):
        self.bdict[b'the'] = b'an'
        self.assertEqual(b'an', self.bdict[b'the'])

    def testCase(self):
        self.bdict[b'The'] = b'De'
        self.bdict[b'the'] = b'de'
        self.assertEqual(b'De', self.bdict[b'The'])
        self.assertEqual(b'de', self.bdict[b'the'])

    def testSpaces(self):
        self.bdict[b'The one'] = b'De ene'
        self.assertEqual(b'De ene', self.bdict[b'The one'])
        
class DoubleUniqueBerkeleyDictTest(BerkeleyDictTestBase):
    def setUp(self):
        BerkeleyDictTestBase.setUp(self)
        self.bdict = DoubleUniqueBerkeleyDict(self.tempdir)

    def testDelete(self):
        BerkeleyDictTestBase.testDelete(self)
        self.assertEqual(None, self.bdict.getKeyFor(b'a string'))

    def testGetKeyFor(self):
        self.bdict[b'1'] = b'one'
        self.bdict[b'2'] = b'two'
        self.assertEqual(b'1', self.bdict.getKeyFor(b'one'))

class BerkeleyDictTest(BerkeleyDictTestBase):
    def setUp(self):
        BerkeleyDictTestBase.setUp(self)
        self.bdict = BerkeleyDict(self.tempdir)
