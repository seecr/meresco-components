## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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
from meresco.components.numeric.convert import Convert

class ConvertTest(TestCase):
    def testConvertOneDecimal(self):
        convert = Convert(1)
        self.assertEqual(10, convert('1'))
        self.assertEqual(10, convert('1.0'))
        self.assertEqual(10, convert('1.0456789'))
        self.assertEqual(10, convert('0.9999999'))
        self.assertEqual(9, convert('0.945'))

    def testConvertNoDecimal(self):
        convert = Convert(0)
        self.assertEqual(1, convert('1.0'))
        self.assertEqual(1, convert('1.0456789'))
        self.assertEqual(1, convert('0.9999999'))
        self.assertEqual(1, convert('1'))
        self.assertEqual(1, convert('0.5'))
        self.assertEqual(1, convert('1.4456789'))
        self.assertEqual(2, convert('1.945'))
        self.assertEqual(2, convert('1.5'))
        self.assertEqual(2, convert('2.4456789'))

    def testConvertDecimalMinus1(self):
        convert = Convert(-1)
        self.assertEqual(0, convert('1.0'))
        self.assertEqual(1, convert('11.0456789'))
        self.assertEqual(0, convert('0.9999999'))
        self.assertEqual(2, convert('19.45'))

    def testStrangeNumbers(self):
        convert = Convert(1)
        self.assertEqual(50, convert('05.0'))
        self.assertEqual(70, convert('007'))
        self.assertEqual(0, convert('-000'))
        
        
