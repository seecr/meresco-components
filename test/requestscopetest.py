## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012-2013, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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
from meresco.core import Observable
from meresco.components import RequestScope

from weightless.core import compose, be

class RequestScopeTest(SeecrTestCase):
    def testEverythingIsPassed(self):
        usedArgsKwargs=[]
        class MyObserver(Observable):
            def handleRequest(innerself, *args, **kwargs):
                usedArgsKwargs.append((args, kwargs))
                yield 'result'
        dna = be((Observable(),
            (RequestScope(),
                (MyObserver(),)
            )
        ))

        result = list(compose(dna.all.handleRequest("an arg", RequestURI='http://www.example.org/path')))

        self.assertEqual(['result'], result)
        self.assertEqual([(("an arg",), dict(RequestURI='http://www.example.org/path'))], usedArgsKwargs)

    def testRequestScopeIsAvailable(self):
        class MyObserver(Observable):
            def handleRequest(self, *args, **kwargs):
                self.do.setArg()
                yield self.call.getArg()
        class SetArgObserver(Observable):
            def setArg(self):
                self.ctx.requestScope["arg"] = "value"
        class GetArgObserver(Observable):
            def getArg(self):
                return self.ctx.requestScope["arg"]

        dna = be((Observable(),
            (RequestScope(),
                (MyObserver(),
                    (SetArgObserver(),),
                    (GetArgObserver(),)
                )
            )
        ))

        result = list(compose(dna.all.handleRequest("a request")))

        self.assertEqual(['value'], result)

    def testRequestScopeIsPerRequest(self):
        class MyObserver(Observable):
            def handleRequest(self, key, value, *args, **kwargs):
                self.do.setArg(key, value)
                yield self.call.getArg()
        class SetArgObserver(Observable):
            def setArg(self, key, value):
                self.ctx.requestScope[key] = value
        class GetArgObserver(Observable):
            def getArg(self):
                return ';'.join('%s=%s' % (k,v) for k,v in list(self.ctx.requestScope.items()))

        dna = be((Observable(),
            (RequestScope(),
                (MyObserver(),
                    (SetArgObserver(),),
                    (GetArgObserver(),)
                )
            )
        ))

        result0 = list(compose(dna.all.handleRequest("key0", "value0")))
        result1 = list(compose(dna.all.handleRequest("key1", "value1")))

        self.assertEqual(['key0=value0'], result0)
        self.assertEqual(['key1=value1'], result1)
        
    def testRequestScopeForEveryMethod(self):
        resultByDo = []
        class MyObserver(Observable):
            def someAnyMethod(self, key, value, *args, **kwargs):
                self.do.setArg(key, value)
                result = self.call.getArg(key)
                return result
                yield
            def someAllMethod(self, key, value, *args, **kwargs):
                self.do.setArg(key, value)
                yield self.call.getArg(key)
            def someCallMethod(self, key, value, *args, **kwargs):
                self.do.setArg(key, value)
                return self.call.getArg(key)
            def someDoMethod(self, key, value, *args, **kwargs):
                self.do.setArg(key, value)
                resultByDo.append(self.call.getArg(key))
        class SetArgObserver(Observable):
            def setArg(self, key, value):
                self.ctx.requestScope[key] = value
        class GetArgObserver(Observable):
            def getArg(self, key):
                return self.ctx.requestScope[key]

        dna = be((Observable(),
            (RequestScope(),
                (MyObserver(),
                    (SetArgObserver(),),
                    (GetArgObserver(),)
                )
            )
        ))

        try:
            next(compose(dna.any.someAnyMethod(key='anykey', value='anyvalue')))
            self.fail()
        except StopIteration as e:
            self.assertEqual('anyvalue', e.args[0])
        self.assertEqual(['allvalue'], list(compose(dna.all.someAllMethod(key='allkey', value='allvalue'))))
        dna.do.someDoMethod(key='dokey', value='dovalue')
        self.assertEqual(['dovalue'], resultByDo)
        self.assertEqual('callvalue', dna.call.someCallMethod(key='callkey', value='callvalue'))
        


