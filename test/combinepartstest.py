## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

from cq2utils import CallTrace
from unittest import TestCase
from meresco.components import CombineParts
from weightless.core import compose

class CombinePartsTest(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.combine = CombineParts({'together':['one', 'two']})
        self.observer = CallTrace('observer')
        self.combine.addObserver(self.observer)
        self.observer.methods['yieldRecord'] = lambda identifier, partname: (f for f in ['<%s/>' % partname])

    def testPassThroughOtherStuff(self):
        result = list(compose(self.combine.yieldRecord(identifier='identifier', partname='partname')))
        self.assertEquals(['<partname/>'], result)
        self.assertEquals(['yieldRecord'], [m.name for m in self.observer.calledMethods])
        self.assertEquals([dict(identifier='identifier', partname='partname')], [m.kwargs for m in self.observer.calledMethods])

    def testTogether(self):
        result = ''.join(compose(self.combine.yieldRecord(identifier='identifier', partname='together')))
        self.assertEquals('<doc:document xmlns:doc="http://meresco.org/namespace/harvester/document"><doc:part name="one"><one/></doc:part><doc:part name="two"><two/></doc:part></doc:document>', result)

        self.assertEquals(['yieldRecord', 'yieldRecord'], [m.name for m in self.observer.calledMethods])
        self.assertEquals([dict(identifier='identifier', partname='one'), dict(identifier='identifier', partname='two')], [m.kwargs for m in self.observer.calledMethods])

    def testTogetherWithOnePartMissingAllowed(self):
        self.combine = CombineParts({'together':['one', 'two']}, allowMissingParts=True)
        self.combine.addObserver(self.observer)
        def yieldRecord(identifier, partname):
            if partname == 'two': 
                raise IOError('two')
            yield '<%s/>' % partname
        self.observer.methods['yieldRecord'] = yieldRecord
        result = ''.join(compose(self.combine.yieldRecord(identifier='identifier', partname='together')))
        self.assertEquals('<doc:document xmlns:doc="http://meresco.org/namespace/harvester/document"><doc:part name="one"><one/></doc:part></doc:document>', result)

    def testTogetherWithOnePartMissingNotAllowed(self):
        def yieldRecord(identifier, partname):
            if partname == 'two': 
                raise IOError('two')
            yield '<%s/>' % partname
        self.observer.methods['yieldRecord'] = yieldRecord
        generator = compose(self.combine.yieldRecord(identifier='identifier', partname='together'))
        self.assertRaises(IOError, generator.next)

