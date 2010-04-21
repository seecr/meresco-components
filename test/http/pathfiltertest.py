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

from cq2utils import CQ2TestCase, CallTrace

from meresco.components.http import PathFilter

class PathFilterTest(CQ2TestCase):
    def testSimplePath(self):
        f = PathFilter('/path')
        interceptor = CallTrace('Interceptor')
        f.addObserver(interceptor)
        list(f.handleRequest(path='/path', otherArgument='value'))
        self.assertEquals(1, len(interceptor.calledMethods))
        self.assertEquals('handleRequest', interceptor.calledMethods[0].name)
        self.assertEquals({'path':'/path', 'otherArgument':'value'}, interceptor.calledMethods[0].kwargs)

    def testOtherPath(self):
        f = PathFilter('/path')
        interceptor = CallTrace('Interceptor')
        f.addObserver(interceptor)
        list(f.handleRequest(path='/other/path'))
        self.assertEquals(0, len(interceptor.calledMethods))

    def testPaths(self):
        f = PathFilter(['/path', '/other/path'])
        interceptor = CallTrace('Interceptor')
        f.addObserver(interceptor)
        list(f.handleRequest(path='/other/path'))
        self.assertEquals(1, len(interceptor.calledMethods))

    def testExcludingPaths(self):
        f = PathFilter('/path', excluding=['/path/not/this'])
        interceptor = CallTrace('Interceptor')
        f.addObserver(interceptor)
        list(f.handleRequest(path='/path/not/this/path'))
        self.assertEquals(0, len(interceptor.calledMethods))
        list(f.handleRequest(path='/path/other'))
        self.assertEquals(1, len(interceptor.calledMethods))
