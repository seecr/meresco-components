## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2006-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2006-2011, 2018 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2011-2013, 2018 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012-2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from meresco.components import SortKeysRename
from meresco.core import Observable
from weightless.core import consume, asList

class SortKeysRenameTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.observer = CallTrace('self.observer')
        self.observer.returnValues['executeQuery'] = (x for x in [(0,[])])
        self.sortKeysRename = SortKeysRename(lambda name: 'new.' + name)
        self.sortKeysRename.addObserver(self.observer)

    def testShouldNotInterfereIfSortKeysIsOmitted(self):
        total, recordIds = asList(self.sortKeysRename.executeQuery(query='AbstractSyntaxTree', start=1, stop=2))[0]
        self.assertEqual(0, total)
        self.assertEqual([], recordIds)
        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertEqual({'query':'AbstractSyntaxTree', 'start':1, 'stop':2, 'sortKeys':None}, self.observer.calledMethods[0].kwargs)

    def testShouldNotInterfereIfSortKeysIsNone(self):
        consume(self.sortKeysRename.executeQuery(query='AbstractSyntaxTree', sortKeys=None))
        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertEqual({'query':'AbstractSyntaxTree', 'sortKeys':None}, self.observer.calledMethods[0].kwargs)

    def testShouldRenameSortKeysFieldname(self):
        consume(self.sortKeysRename.executeQuery(query='AbstractSyntaxTree', sortKeys=[{'sortBy':'sortKeys', 'sortDescending': True}]))
        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertEqual({'query':'AbstractSyntaxTree', 'sortKeys':[{'sortBy':'new.sortKeys', 'sortDescending': True}]}, self.observer.calledMethods[0].kwargs)

    def testShouldBeTransparent(self):
        start = Observable()
        start.addObserver(self.sortKeysRename)
        self.observer.returnValues['someMethod'] = 'someResult'
        self.assertEqual('someResult', start.call.someMethod('someParameter'))
        
