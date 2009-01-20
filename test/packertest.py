# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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

from cq2utils import CQ2TestCase

from merescocomponents.packer import IntStringPacker, IntPacker, StringIntPacker

class PackerTest(CQ2TestCase):
    def assertPacking(self, item):
        packed = self.packer.pack(item)
        result = self.packer.unpack(packed)
        self.assertEquals(item, result)
        self.assertEquals(len(packed), self.packer.length)

    def assertError(self, item):
        try:
            self.packer.pack(item)
            self.fail()
        except TypeError, e:
            pass
        
    def testIntPacker(self):
        self.packer = IntPacker()
        self.assertPacking(1)
        self.assertPacking(12345678901234567890)
        self.assertError(-1)

    def testIntStringPacker(self):
        self.packer = IntStringPacker()
        self.assertPacking((1234, 'eenstring'))
        self.assertPacking((10, 'Äb©dé'))
        self.assertPacking((10, u'Äb©dé'))
        self.assertError((10, 400 * 'a'))
        
    def testStringIntPacker(self):
        self.packer = StringIntPacker()
        self.assertPacking(('eenstring', 1234))
        self.assertPacking(('Äb©dé', 10))
        self.assertPacking((u'Äb©dé', 10))
        self.assertError((400 * 'a', 10))
        