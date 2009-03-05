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


from cq2utils import CQ2TestCase

from merescocomponents.oai import BerkeleyDict

class BerkeleyDictTest(CQ2TestCase):
    def testInsert(self):
        d = BerkeleyDict(self.tempdir)
        d['1'] = 'some string'
        self.assertEquals('some string', d['1'])
        d['1'] = 'some other string'
        self.assertEquals('some other string', d['1'])

    def testNoneExistingKey(self):
        d = BerkeleyDict(self.tempdir)
        try:
            d['not']
            self.fail()
        except KeyError:
            pass

    def testDelete(self):
        d = BerkeleyDict(self.tempdir)
        d['1'] = 'a string'
        self.assertEquals('a string', d['1'])
        del d['1']
        try:
            d['1']
            self.fail('must not come here')
        except KeyError:
            pass

    def testGet(self):
        d = BerkeleyDict(self.tempdir)
        d['1'] = 'some other string'

        self.assertEquals('some other string', d.get('1', 'something'))
        self.assertEquals('something', d.get('2', 'something'))

    def testGetKeys(self):
        d = BerkeleyDict(self.tempdir)
        d['1'] = 'one'
        d['2'] = 'two'
        self.assertEquals('1', d.getKeyFor('one'))

    def testStopWord(self):
        d = BerkeleyDict(self.tempdir)
        d['the'] = 'an'
        self.assertEquals('an', d['the'])

    def testCase(self):
        d = BerkeleyDict(self.tempdir)
        d['The'] = 'De'
        d['the'] = 'de'
        self.assertEquals('De', d['The'])
        self.assertEquals('de', d['the'])

    def testSpaces(self):
        d = BerkeleyDict(self.tempdir)
        d['The one'] = 'De ene'
        self.assertEquals('De ene', d['The one'])

#items()¶
#keys()¶
#values()¶
