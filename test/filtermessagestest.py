## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012, 2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
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
        self.observer2 = object()
        self.observer3 = CallTrace(
            'observer3',
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
            ),
            (FilterMessages(allowed=['message', 'function', 'gen', 'noop']),
                (self.observer3,)
            )
        ))


    def testAll(self):
        list(compose(self.dna.all.message()))
        self.assertEqual([], [m.name for m in self.observer1.calledMethods])
        self.assertEqual(['message'], [m.name for m in self.observer3.calledMethods])

    def testCall(self):
        self.assertEqual(42, self.dna.call.function())

    def testDo(self):
        self.dna.do.noop()
        self.assertEqual([], [m.name for m in self.observer1.calledMethods])
        self.assertEqual(['noop'], [m.name for m in self.observer3.calledMethods])

    def testAny(self):
        self.assertEqual([42], list(compose(self.dna.any.gen())))

    def testEitherAllowedOrDisallowed(self):
        self.assertRaises(ValueError, lambda: FilterMessages(allowed=['either'], disallowed=['or']))
