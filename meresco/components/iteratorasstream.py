## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
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


class IteratorAsStream(object):
    def __init__(self, iterator):
        self._iterator = iter(iterator)
        self._leftover = ''

    def read(self, size=None):
        if size is None or size < 0:
            data = self._leftover
            self._leftover = ''
            return data + ''.join(self._iterator)
        while len(self._leftover) < size:
            try:
                self._leftover += self._iterator.next()
            except StopIteration:
                break
        data = self._leftover[:size]
        self._leftover = self._leftover[size:]
        return data

    def next(self):
        if self._leftover:
            data = self._leftover
            self._leftover = ''
            return data
        return self._iterator.next()

    def __iter__(self):
        return self

        

