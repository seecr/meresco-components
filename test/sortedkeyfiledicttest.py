## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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

from merescocomponents import SortedKeyFileDict
from os.path import join

class SortedKeyFileDictTest(CQ2TestCase):
    def testSortedKeyFileDictI2S(self):
        d = SortedKeyFileDict(join(self.tempdir, 'dict'), 'Integer2String', initialContent=[(1,'value One'),(3,'value Three')])

        self.assertEquals('value One', d[1])
        self.assertEquals('value Three', d[3])

        self.assertKeyError(d, 0)
        self.assertKeyError(d, 2)
        self.assertKeyError(d, 4)

        self.assertEquals('value One', d.get(1, 'default'))
        self.assertEquals('default', d.get(2, 'default'))

        self.assertEquals([(1,'value One'),(3,'value Three')], list(d.items()))
        self.assertEquals(['value One', 'value Three'], list(d.values()))
        self.assertEquals([1,3], list(d.keys()))
        
    def assertKeyError(self, aDict, key):
        try:
            aDict[key]
            self.fail('KeyError expected')
        except KeyError:
            pass

    def testSortedKeyFileDictS2I(self):
        d = SortedKeyFileDict(join(self.tempdir, 'dict'), 'String2Integer', initialContent=[('one',1),('three',3)])
        
        self.assertEquals(1, d['one'])
        self.assertEquals(3, d['three'])

        self.assertKeyError(d, 'not')
        self.assertKeyError(d, 'pass')
        self.assertKeyError(d, 'unstored')

        self.assertEquals(1, d.get('one', 0))
        self.assertEquals(0, d.get('two', 0))

        self.assertEquals([('one', 1),('three', 3)], list(d.items()))
        self.assertEquals(['one', 'three'], list(d.keys()))
        self.assertEquals([1,3], list(d.values()))

    def testRewriteDictionary(self):
        d = SortedKeyFileDict(join(self.tempdir, 'dict'), 'Integer2String', initialContent=[(1,'value One'),(2, 'value Two'), (3,'value Three')])
        self.assertEquals([1,2,3], list(d.keys()))

        d = SortedKeyFileDict(join(self.tempdir, 'dict'), 'Integer2String', initialContent=((key, value) for key, value in d.items() if key != 2))
        self.assertEquals([1,3], list(d.keys()))

    def testEmptyDictionary(self):
        d = SortedKeyFileDict(join(self.tempdir, 'dict'), 'String2Integer', initialContent=None)
        
        self.assertKeyError(d, 'not')
        self.assertEquals([], list(d.items()))
        self.assertEquals([], list(d.keys()))
        self.assertEquals([], list(d.values()))
        
        
