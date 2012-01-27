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
from meresco.components import FilterPartByName
from weightless.core import compose

class FilterPartByNameTest(TestCase):
    def testFilterIncluded(self):
        filter = FilterPartByName(included=['thisone'])
        observer = CallTrace('observer')
        observer.methods['yieldRecord'] = lambda **kwargs: (f for f in ['data'])
        filter.addObserver(observer)

        self.assertEquals(['data'], list(compose(filter.yieldRecord(identifier='identifier', partname='thisone'))))
        self.assertEquals([], list(compose(filter.yieldRecord(identifier='identifier', partname='no'))))

    def testFilterExcluded(self):
        filter = FilterPartByName(excluded=['thisone'])
        observer = CallTrace('observer')
        observer.methods['yieldRecord'] = lambda **kwargs: (f for f in ['data'])
        filter.addObserver(observer)

        self.assertEquals([], list(compose(filter.yieldRecord(identifier='identifier', partname='thisone'))))
        self.assertEquals(['data'], list(compose(filter.yieldRecord(identifier='identifier', partname='no'))))
    
    def testFilter(self):
        self.assertRaises(ValueError, FilterPartByName)

    def testFilterOnAdd(self):
        filter = FilterPartByName(included=['thisone'])
        observer = CallTrace('observer')
        observer.methods['add'] = lambda **kwargs: (f for f in [])
        filter.addObserver(observer)

        self.assertEquals([], list(compose(filter.add(identifier='identifier', partname='thisone'))))
        self.assertEquals(['add'], [m.name for m in observer.calledMethods])
        del observer.calledMethods[:]
        self.assertEquals([], list(compose(filter.add(identifier='identifier', partname='no'))))
        self.assertEquals([], [m.name for m in observer.calledMethods])
