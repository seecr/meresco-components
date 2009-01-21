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

from filelist import SortedFileList
from packer import IntStringPacker, StringIntPacker
from bisect import bisect_left

PACKERS = {
    'Integer2String': (IntStringPacker(), ''),
    'String2Integer': (StringIntPacker(), 0)
}

class SortedKeyFileDict(object):
    def __init__(self, filename, dictFormat, initialContent=[]):
        packer, self._emptyValue = PACKERS[dictFormat]
        self._list = SortedFileList(filename, initialContent=initialContent, packer=packer)

    def __getitem__(self, key):
        index = bisect_left(self._list, (key, self._emptyValue))
        if index == len(self._list):
            raise KeyError(key)
        storedKey, value = self._list[index]
        if storedKey != key:
            raise KeyError(key)
        return value

    def get(self, key, defaultValue=None):
        try:
            return self[key]
        except KeyError:
            return defaultValue

    def items(self):
        return iter(self._list)

    def keys(self):
        for key,value in self._list:
            yield key

    def values(self):
        for key,value in self._list:
            yield value
