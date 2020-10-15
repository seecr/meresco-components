## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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
from os.path import join

from meresco.components.contextset import ContextSet, ContextSetException, ContextSetList
from io import StringIO

class ContextSetTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        stream = StringIO("""
# test contextset file
query.field1\tactualfield1
field1 actualfield1
field2  actualfield2
field2    actualotherfield2

""")
        self.set = ContextSet('test', stream)

    def testLookup(self):
        self.assertEqual('test', self.set.name)
        self.assertEqual('actualfield1', self.set.lookup('test.query.field1'))
        self.assertEqual('actualfield1', self.set.lookup('test.field1'))
        self.assertEqual('actualfield2', self.set.lookup('test.field2'))
        self.assertEqual('nosuchfield', self.set.lookup('nosuchfield'))
        self.assertEqual('test.nosuchfield', self.set.lookup('test.nosuchfield'))
        self.assertEqual('otherset.field', self.set.lookup('otherset.field'))

    def testLookupInList(self):
        setlist = ContextSetList()
        setlist.add(ContextSet('set1', StringIO("field\tactualfield\nfield1\tactualfield1")))
        setlist.add(ContextSet('set2', StringIO("field\tactualfield\nfield2\tactualfield2")))
        self.assertEqual('actualfield', setlist.lookup('set1.field'))
        self.assertEqual('actualfield', setlist.lookup('set2.field'))
        self.assertEqual('actualfield2', setlist.lookup('set2.field2'))
        self.assertEqual('unsupportedset.field3', setlist.lookup('unsupportedset.field3'))


