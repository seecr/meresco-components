## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
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
from unittest import TestCase
from cq2utils import CallTrace
from meresco.components.http import PathRename
from meresco.core import Observable
from weightless import compose

class PathRenameTest(TestCase):
    def testRename(self):
        rename = PathRename(lambda path: '/new'+path)
        interceptor = CallTrace('interceptor')
        rename.addObserver(interceptor)

        list(compose(rename.handleRequest(path='/mypath')))

        self.assertEquals(1, len(interceptor.calledMethods))
        self.assertEquals("handleRequest(path='/new/mypath')", str(interceptor.calledMethods[0]))

    def testTransparency(self):
        observable = Observable()
        rename = PathRename(lambda path: '/new'+path)
        interceptor = CallTrace('interceptor')
        observable.addObserver(rename)
        rename.addObserver(interceptor)

        observable.do.otherMethod('attribute')

        self.assertEquals(1, len(interceptor.calledMethods))
        self.assertEquals("otherMethod('attribute')", str(interceptor.calledMethods[0]))
