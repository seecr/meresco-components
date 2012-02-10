## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
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

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import compose, be
from meresco.core import Observable
from meresco.components import FilterMessages


class FilterMessagesTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.observer1 = CallTrace(
            'observer1', 
            emptyGeneratorMethods=['message'], 
            returnValues={
                'function': 41, 
                'gen': (i for i in [41]),
                'noop': None
            }
        )
        self.observer2 = CallTrace(
            'observer2', 
            emptyGeneratorMethods=['message'], 
            returnValues={
                'function': 42, 
                'gen': (i for i in [42]),
                'noop': None
            }
        )
        self.dna = be((Observable(),
            (FilterMessages(disallowed=['message', 'function', 'gen', 'noop']),
                (self.observer1,)
            ),
            (FilterMessages(allowed=['message', 'function', 'gen', 'noop']),
                (self.observer2,)
            )
        ))


    def testAll(self):
        list(compose(self.dna.all.message()))
        self.assertEquals([], [m.name for m in self.observer1.calledMethods])
        self.assertEquals(['message'], [m.name for m in self.observer2.calledMethods])

    def testCall(self):
        self.assertEquals(42, self.dna.call.function())

    def testDo(self):
        self.dna.do.noop()
        self.assertEquals([], [m.name for m in self.observer1.calledMethods])
        self.assertEquals(['noop'], [m.name for m in self.observer2.calledMethods])

    def testAny(self):
        self.assertEquals([42], list(compose(self.dna.any.gen())))

