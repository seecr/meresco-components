## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012, 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2016 SURFmarket https://surf.nl
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

from meresco.components.http import PathFilter
from weightless.core import consume

class PathFilterTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.interceptor = CallTrace('Interceptor', methods={'handleRequest': lambda *args, **kwargs: (x for x in [])})

    def testSimplePath(self):
        f = PathFilter('/path')
        f.addObserver(self.interceptor)
        consume(f.handleRequest(path='/path', otherArgument='value'))
        self.assertEquals(1, len(self.interceptor.calledMethods))
        self.assertEquals('handleRequest', self.interceptor.calledMethods[0].name)
        self.assertEquals({'path':'/path', 'otherArgument':'value'}, self.interceptor.calledMethods[0].kwargs)

    def testOtherPath(self):
        f = PathFilter('/path')
        f.addObserver(self.interceptor)
        consume(f.handleRequest(path='/other/path'))
        self.assertEquals(0, len(self.interceptor.calledMethods))

    def testPaths(self):
        f = PathFilter(['/path', '/other/path'])
        f.addObserver(self.interceptor)
        consume(f.handleRequest(path='/other/path'))
        self.assertEquals(1, len(self.interceptor.calledMethods))

    def testExcludingPaths(self):
        f = PathFilter('/path', excluding=['/path/not/this'])
        f.addObserver(self.interceptor)
        consume(f.handleRequest(path='/path/not/this/path'))
        self.assertEquals(0, len(self.interceptor.calledMethods))
        consume(f.handleRequest(path='/path/other'))
        self.assertEquals(1, len(self.interceptor.calledMethods))

    def testUpdatePaths(self):
        f = PathFilter('/')
        f.addObserver(self.interceptor)
        f.updatePaths('/path', excluding=['/path/not/this'])
        consume(f.handleRequest(path='/path/not/this/path'))
        self.assertEquals(0, len(self.interceptor.calledMethods))
        consume(f.handleRequest(path='/path/other'))
        self.assertEquals(1, len(self.interceptor.calledMethods))
