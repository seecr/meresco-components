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

from unittest import TestCase
from meresco.components.numeric.convert import Convert

class ConvertTest(TestCase):
    def testConvertOneDecimal(self):
        convert = Convert(1)
        self.assertEquals(10, convert('1'))
        self.assertEquals(10, convert('1.0'))
        self.assertEquals(10, convert('1.0456789'))
        self.assertEquals(10, convert('0.9999999'))
        self.assertEquals(9, convert('0.945'))

    def testConvertNoDecimal(self):
        convert = Convert(0)
        self.assertEquals(1, convert('1.0'))
        self.assertEquals(1, convert('1.0456789'))
        self.assertEquals(1, convert('0.9999999'))
        self.assertEquals(1, convert('1'))
        self.assertEquals(1, convert('0.5'))
        self.assertEquals(1, convert('1.4456789'))
        self.assertEquals(2, convert('1.945'))
        self.assertEquals(2, convert('1.5'))
        self.assertEquals(2, convert('2.4456789'))

    def testConvertDecimalMinus1(self):
        convert = Convert(-1)
        self.assertEquals(0, convert('1.0'))
        self.assertEquals(1, convert('11.0456789'))
        self.assertEquals(0, convert('0.9999999'))
        self.assertEquals(2, convert('19.45'))

    def testStrangeNumbers(self):
        convert = Convert(1)
        self.assertEquals(50, convert('05.0'))
        self.assertEquals(70, convert('007'))
        self.assertEquals(0, convert('-000'))
        
        
