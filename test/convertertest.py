# encoding=utf-8
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

from weightless.core import be, compose
from meresco.core import Observable

from meresco.components import Converter


class FourtytwoConverter(Converter):
    def _convert(self, value):
        return 42

class ConverterTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.observer1 = CallTrace('observer 1', returnValues={
            'f': (i for i in ['done']),
            'g': 'done'}, onlySpecifiedMethods=True)
        self.observer2 = CallTrace('observer 2', returnValues={
            'h': 'done2'}, onlySpecifiedMethods=True)
        self.observable = be(
            (Observable(),
                (FourtytwoConverter(fromKwarg='data', toKwarg='fourtytwo'),
                    (self.observer2, )
                ),
                (self.observer1, )
            )
        )

    def testNoneOfTheObserversRespondTransparency(self):
        self.assertEquals(['done'], list(compose(self.observable.any.f(data=41))))
        self.assertEquals('done', self.observable.call.g(data=41))
        self.assertEquals('done2', self.observable.call.h(data=41))

        self.assertEquals(2, len(self.observer1.calledMethods))
        self.assertEquals({'data': 41}, self.observer1.calledMethods[0].kwargs)
        self.assertEquals({'data': 41}, self.observer1.calledMethods[1].kwargs)
        self.assertEquals(1, len(self.observer2.calledMethods))
        self.assertEquals({'fourtytwo': 42}, self.observer2.calledMethods[0].kwargs)

    def testFromKwargMustBeSpecified(self):
        self.assertRaises(ValueError, lambda: FourtytwoConverter(fromKwarg=None))

