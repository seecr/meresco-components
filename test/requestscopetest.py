## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from cq2utils import CQ2TestCase
from meresco.core import Observable
from meresco.components import RequestScope

class RequestScopeTest(CQ2TestCase):
    def testEverythingIsPassed(self):
        usedArgsKwargs=[]
        class MyObserver(Observable):
            def handleRequest(innerself, *args, **kwargs):
                usedArgsKwargs.append((args, kwargs))
                yield 'result'
        r = RequestScope()
        r.addObserver(MyObserver())

        result = list(r.handleRequest("an arg", RequestURI='http://www.example.org/path'))

        self.assertEquals(['result'], result)
        self.assertEquals([(("an arg",), dict(RequestURI='http://www.example.org/path'))], usedArgsKwargs)

    def testRequestScopeIsAvailable(self):
        class MyObserver(Observable):
            def handleRequest(self, *args, **kwargs):
                self.do.setArg()
                yield self.any.getArg()
        class SetArgObserver(Observable):
            def setArg(self):
                self.ctx.requestScope["arg"] = "value"
        class GetArgObserver(Observable):
            def getArg(self):
                return self.ctx.requestScope["arg"]

        r = RequestScope()
        myObserver = MyObserver()
        myObserver.addObserver(SetArgObserver())
        myObserver.addObserver(GetArgObserver())
        r.addObserver(myObserver)

        result = list(r.handleRequest("a request"))

        self.assertEquals(['value'], result)

    def testRequestScopeIsPerRequest(self):
        class MyObserver(Observable):
            def handleRequest(self, key, value, *args, **kwargs):
                self.do.setArg(key, value)
                yield self.any.getArg()
        class SetArgObserver(Observable):
            def setArg(self, key, value):
                self.ctx.requestScope[key] = value
        class GetArgObserver(Observable):
            def getArg(self):
                return ';'.join('%s=%s' % (k,v) for k,v in self.ctx.requestScope.items())

        r = RequestScope()
        myObserver = MyObserver()
        myObserver.addObserver(SetArgObserver())
        myObserver.addObserver(GetArgObserver())
        r.addObserver(myObserver)

        result0 = list(r.handleRequest("key0", "value0"))
        result1 = list(r.handleRequest("key1", "value1"))

        self.assertEquals(['key0=value0'], result0)
        self.assertEquals(['key1=value1'], result1)
        
