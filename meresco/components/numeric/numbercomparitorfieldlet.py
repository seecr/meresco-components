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

from meresco.core import Observable
from convert import Convert
from math import ceil, log
from util import Util

class NumberComparitorFieldlet(Observable):
    def __init__(self, nrOfDecimals, valueLength):
        Observable.__init__(self)
        assert valueLength > 0, 'The length of values stored should be at least 1'
        self._convert = Convert(nrOfDecimals)
        self._valueLength = valueLength
        self._util = Util(valueLength)

    def addField(self, name, value):
        value = self._convert(value)
        if not 0 <= value < self._util.maximum:
            raise ValueError('Expected 0 <= value <= %s, but value was "%s"' % (self._util.maximum, value))

        for decimalPosition in range(self._valueLength):
            template = self._util.template(decimalPosition)
            decimal = self._util.decimal(value, decimalPosition)
            for i in range(0, decimal + 1):
                self.do.addField('%s.gte' % name, template % self._util.VALUES[i])
            for i in range(decimal, self._util.base):
                self.do.addField('%s.lte' % name, template % self._util.VALUES[i])

