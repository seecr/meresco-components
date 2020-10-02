## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011, 2017 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012, 2017 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2017 SURF http://www.surf.nl
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

from unittest import TestCase
from seecr.test import CallTrace
from meresco.components.http import PathRename
from meresco.core import Observable
from weightless.core import compose

class PathRenameTest(TestCase):
    def testRename(self):
        rename = PathRename(lambda path: '/new'+path)
        interceptor = CallTrace('interceptor', methods={'handleRequest': lambda *args, **kwargs: (x for x in [])})
        rename.addObserver(interceptor)

        list(compose(rename.handleRequest(path='/mypath')))

        self.assertEqual(['handleRequest'], interceptor.calledMethodNames())
        self.assertEqual(dict(originalPath='/mypath', path='/new/mypath'), interceptor.calledMethods[0].kwargs)

    def testTransparency(self):
        observable = Observable()
        rename = PathRename(lambda path: '/new'+path)
        interceptor = CallTrace('interceptor')
        observable.addObserver(rename)
        rename.addObserver(interceptor)

        observable.do.otherMethod('attribute')

        self.assertEqual(1, len(interceptor.calledMethods))
        self.assertEqual("otherMethod('attribute')", str(interceptor.calledMethods[0]))

    def testOriginalPathAlreadyUsed(self):
        rename = PathRename(lambda path: '/new'+path)
        interceptor = CallTrace('interceptor', methods={'handleRequest': lambda *args, **kwargs: (x for x in [])})
        rename.addObserver(interceptor)

        list(compose(rename.handleRequest(path='/mypath', originalPath='/original/path')))

        self.assertEqual(['handleRequest'], interceptor.calledMethodNames())
        self.assertEqual(dict(originalPath='/original/path', path='/new/mypath'), interceptor.calledMethods[0].kwargs)

