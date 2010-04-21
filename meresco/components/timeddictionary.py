## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
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
from time import time

class TimedDictionary(object):
    def __init__(self, timeout):
        self._timeout = timeout
        self._dictionary = {}
        self._list = []

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def getTime(self, key):
        return self._dictionary[key][0]

    def purge(self):
        now = self._now()
        index = 0
        for i, key in enumerate(self._list):
            if self.hasExpired(key, now):
                del self._dictionary[key]
                index = i + 1
            else:
                break
        if index > 0:
            self._list = self._list[index:]

    def touch(self, key):
        self._dictionary[key] = (self._now(), self._dictionary[key][1])
        self._list.remove(key)
        self._list.append(key)

    def hasExpired(self, key, time=None):
        if not time:
            time = self._now()
        return time > self.getTime(key) + self._timeout

    def _now(self):
        return time()

    def __getitem__(self, key):
        if self.hasExpired(key):
            del self[key]
        ignoredTime, value = self._dictionary[key]
        return value

    def __setitem__(self, key, value):
        self.purge()
        if key in self:
            self._list.remove(key)
        self._dictionary[key] = (self._now(), value)
        self._list.append(key)

    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            return False
    has_key = __contains__

    def __delitem__(self, key):
        del self._dictionary[key]
        self._list.remove(key)
