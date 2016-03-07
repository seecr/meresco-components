## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2011-2012, 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from seecr.test import CallTrace, SeecrTestCase
from meresco.components import CombineParts

class CombinePartsTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.combine = CombineParts({'together':['one', 'two']})
        self.observer = CallTrace('observer')
        self.combine.addObserver(self.observer)
        self.observer.methods['getData'] = lambda identifier, name: '<%s/>' % name

    def testPassThroughOtherStuff(self):
        result = self.combine.getData(identifier='identifier', name='name')
        self.assertEquals('<name/>', result)
        self.assertEquals(['getData'], self.observer.calledMethodNames())
        self.assertEquals([dict(identifier='identifier', name='name')], [m.kwargs for m in self.observer.calledMethods])

    def testTogether(self):
        result = self.combine.getData(identifier='identifier', name='together')
        expected = '<doc:document xmlns:doc="http://meresco.org/namespace/harvester/document"><doc:part name="one"><one/></doc:part><doc:part name="two"><two/></doc:part></doc:document>'
        self.assertEquals(expected, result)

        self.assertEquals(['getData', 'getData'], self.observer.calledMethodNames())
        self.assertEquals([dict(identifier='identifier', name='one'), dict(identifier='identifier', name='two')], [m.kwargs for m in self.observer.calledMethods])

    def testTogetherWithOnePartMissingAllowed(self):
        self.combine = CombineParts({'together':['one', 'two']}, allowMissingParts=['two'])
        self.combine.addObserver(self.observer)
        def getData(identifier, name):
            if name == 'two':
                raise KeyError('two')
            return '<%s/>' % name
        self.observer.methods['getData'] = getData
        result = self.combine.getData(identifier='identifier', name='together')
        self.assertEquals('<doc:document xmlns:doc="http://meresco.org/namespace/harvester/document"><doc:part name="one"><one/></doc:part></doc:document>', result)

    def testTogetherWithOnePartMissingNotAllowed(self):
        def getData(identifier, name):
            if name == 'two':
                raise KeyError('two')
            return '<%s/>' % name
        self.observer.methods['getData'] = getData
        self.assertRaises(KeyError, lambda: self.combine.getData(identifier='identifier', name='together'))

    def testTogetherWithGivenMissingPartsAllowed(self):
        self.combine = CombineParts({'together':['one', 'two']}, allowMissingParts=['two'])
        self.combine.addObserver(self.observer)
        def getData(identifier, name):
            if name == 'one':
                raise KeyError('one')
            return '<%s/>' % name
        self.observer.methods['getData'] = getData
        self.assertRaises(KeyError, lambda: self.combine.getData(identifier='identifier', name='together'))

