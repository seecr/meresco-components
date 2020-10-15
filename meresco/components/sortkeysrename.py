## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2006-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2006-2011, 2018 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2011-2013, 2018, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from meresco.core import Transparent

class SortKeysRename(Transparent):
    def __init__(self, rename):
        Transparent.__init__(self)
        self._rename = rename

    def executeQuery(self, sortKeys=None, *args, **kwargs):
        if not sortKeys is None:
            newSortKeys = []
            for sortKey in sortKeys:
                sortKey = sortKey.copy()
                sortKey['sortBy'] = self._rename(sortKey['sortBy'])
                newSortKeys.append(sortKey)
            sortKeys = newSortKeys
        response = yield self.any.executeQuery(sortKeys=sortKeys, *args, **kwargs)
        return response

