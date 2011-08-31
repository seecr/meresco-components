## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
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

from meresco.core import be, Observable

from meresco.components import CacheComponent

from cq2utils import CQ2TestCase, CallTrace
from time import sleep

class CacheComponentTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.cacheComponent = CacheComponent(timeout=10, methodName="someMethod", keyKwarg="argument")
        self.observer = CallTrace(returnValues=dict(someMethod="result", anotherMethod="anotherResult"))

        self.dna = be(
            (Observable(),
                (self.cacheComponent,
                    (self.observer,)
                )
            )
        )

    def testPassThrough(self):
        result = self.dna.any.anotherMethod(1, True, argument="first")
        self.assertEquals("anotherResult", result)
        self.assertEquals(["anotherMethod(1, <class True>, argument='first')"], [str(x) for x in self.observer.calledMethods])
        
    def testPassThrough2(self):
        self.observer.ignoredAttributes = ['yetAnotherMethod']
        try:
            result = self.dna.any.yetAnotherMethod(1, True, argument="first")
            self.fail()
        except AttributeError, e:
            self.assertEquals("None of the 1 observers responds to any.yetAnotherMethod(...)", str(e))

    def testPlayNicelyWithOthers(self):
        cacheComponent = CacheComponent(timeout=10, methodName="someMethod", keyKwarg="argument")
        observer1 = CallTrace("One")
        observer1.ignoredAttributes = ['someMethod']
        observer2 = CallTrace("Two")
        observer2.returnValues['someMethod'] = 'someResult'
        observer3 = CallTrace("Three")
        observer3.returnValues['someMethod'] = 'someOtherResult'

        dna = be(
            (Observable(),
                (observer1,),
                (cacheComponent,
                    (observer2,)
                ),
                (observer3,)
            )
        )
       
        result = dna.any.someMethod(argument="value")
        self.assertEquals('someResult', result)
        
        result = list(dna.all.someMethod(argument="value"))
        self.assertEquals(['someResult', 'someOtherResult'], result)


    def testCaching(self):
        result = self.dna.any.someMethod(argument="first")
        self.assertEquals("result", result)
        self.assertEquals(1, len(self.observer.calledMethods))
        result = self.dna.any.someMethod(argument="first")
        self.assertEquals("result", result)
        self.assertEquals(1, len(self.observer.calledMethods))

    def testKeysTimeOut(self):
        self.cacheComponent._cache._timeout=1
        counter = []
        def someMethod(argument):
            counter.append(True)
            return len(counter)
        self.observer.someMethod=someMethod
        result = self.dna.any.someMethod(argument="first")
        self.assertEquals(1, result)
        result = self.dna.any.someMethod(argument="first")
        self.assertEquals(1, result)
        self.cacheComponent._cache._timeout=.1
        sleep(.2)
        result = self.dna.any.someMethod(argument="first")
        self.assertEquals(2, result)
