# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012-2013, 2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import CallTrace
from unittest import TestCase
from meresco.core import Observable, asyncnoreturnvalue

from meresco.components import RewritePartname
from weightless.core import compose

class RewritePartnameTest(TestCase):
    def testAddPartname(self):
        @asyncnoreturnvalue
        def add(**kwargs):
            pass
        observable = Observable()
        observer = CallTrace('observer', methods={'add': add})
        rewrite = RewritePartname('newPartname')
        rewrite.addObserver(observer)
        observable.addObserver(rewrite)

        result = list(compose(observable.all.add(identifier='identifier', partname='oldPartname', data='data')))

        self.assertEquals(['add'], [m.name for m in observer.calledMethods])
        self.assertEquals({'identifier': 'identifier', 'partname': 'newPartname', 'data': 'data'}, observer.calledMethods[0].kwargs)
        self.assertEquals([], result)

    def testGetDataPartname(self):
        def getData(**kwargs):
            return 'data'
        observable = Observable()
        observer = CallTrace('observer', methods={'getData': getData})
        rewrite = RewritePartname('newPartname')
        rewrite.addObserver(observer)
        observable.addObserver(rewrite)

        result = observable.call.getData(identifier='identifier', name='oldPartname')

        self.assertEquals(['getData'], [m.name for m in observer.calledMethods])
        self.assertEquals({'identifier': 'identifier', 'name': 'newPartname'}, observer.calledMethods[0].kwargs)
        self.assertEquals('data', result)

