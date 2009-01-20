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
from struct import pack as struct_pack, unpack as struct_unpack, calcsize

class IntPacker(object):
    def __init__(self):
        self._packing = 'Q'
        self.length = calcsize(self._packing)
    
    def pack(self, item):
        return struct_pack(self._packing, item)
    
    def unpack(self, aString):
        (result,) = struct_unpack(self._packing, aString)
        return result

class IntStringPacker(object):
    def __init__(self):
        self._maxStringLength=300
        self._packing = 'Q%dsI' % self._maxStringLength
        self.length = calcsize(self._packing)
    
    def pack(self, item):
        anInt, aString = item
        if len(aString) > self._maxStringLength:
            raise TypeError('string exceeded maximumlength of %d' % self._maxStringLength)
        return struct_pack(self._packing, anInt, str(aString), len(str(aString)))
    
    def unpack(self, packed):
        anInt, aString, stringLength = struct_unpack(self._packing, packed)
        return anInt, aString[:stringLength]

class StringIntPacker(object):
    def __init__(self):
        self._maxStringLength=300
        self._packing = '%dsIQ' % self._maxStringLength
        self.length = calcsize(self._packing)
    
    def pack(self, item):
        aString, anInt = item
        if len(aString) > self._maxStringLength:
            raise TypeError('string exceeded maximumlength of %d' % self._maxStringLength)
        return struct_pack(self._packing, str(aString), len(str(aString)), anInt)
    
    def unpack(self, packed):
        aString, stringLength, anInt = struct_unpack(self._packing, packed)
        return aString[:stringLength], anInt
