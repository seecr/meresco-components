# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
#    Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
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

from cq2utils import CallTrace
from unittest import TestCase
from meresco.core import Observable

from meresco.components import RewritePartname

class RewritePartnameTest(TestCase):
    def testAddPartname(self):
        observable = Observable()
        observer = CallTrace('observer')
        callable = lambda: 42
        observer.returnValues['add'] = callable
        rewrite = RewritePartname('newPartname')
        rewrite.addObserver(observer)
        observable.addObserver(rewrite)

        result = list(observable.all.add(identifier='identifier', partname='oldPartname', data='data'))

        self.assertEquals(['add'], [m.name for m in observer.calledMethods])
        self.assertEquals({'identifier': 'identifier', 'partname': 'newPartname', 'data': 'data'}, observer.calledMethods[0].kwargs)
        self.assertEquals([callable], result)
        
