## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012, 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2016 Stichting Kennisnet http://www.kennisnet.nl
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

from time import time
from warnings import warn

from pylru import lrucache


class TimedDictionary(object):
    def __init__(self, timeout, lruMaxSize=None):
        self._timeout = timeout
        self._dictionary = {} if lruMaxSize is None else lrucache(lruMaxSize)
        self._times = {}
        self._expirationOrder = []

    def __len__(self):
        return self.size()

    def __getitem__(self, key):
        if self.hasExpired(key):
            del self[key]
        return self._dictionary[key]

    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            return False
    has_key = __contains__

    def __setitem__(self, key, value):
        self.purge()
        try:
            self._expirationOrder.remove(key)
        except ValueError:
            pass
        self._times[key] = self._now()
        self._expirationOrder.append(key)
        self._dictionary[key] = value

    def __delitem__(self, key):
        del self._dictionary[key]
        del self._times[key]
        self._expirationOrder.remove(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self):
        return list(self._dictionary.keys())

    def clear(self):
        self._dictionary.clear()
        self._times.clear()
        del self._expirationOrder[:]


    def size(self):
        self.purge()
        return len(self._dictionary)

    def peek(self, key):
        """Provides a way to access values that might expire if accessed normally."""
        return self._dictionary[key]

    def hasExpired(self, key, time=None):
        if not time:
            time = self._now()
        return time > self._times[key] + self._timeout

    def touch(self, key):
        self[key] = self._dictionary[key]

    def purge(self):
        now = self._now()
        index = 0
        for i, key in enumerate(self._expirationOrder):
            if self.hasExpired(key, now) or not key in self._dictionary:
                try:
                    del self._times[key]
                    del self._dictionary[key]
                except:
                    pass
                index = i + 1
            else:
                break
        if index > 0:
            self._expirationOrder = self._expirationOrder[index:]

    def setTimeout(self, timeout):
        self._timeout = timeout

    def getTime(self, key):
        warn('getTime is deprecated (why expose?)', DeprecationWarning)
        _ = self._dictionary[key]  # forcing KeyError if no longer available
        return self._times[key]

    def _now(self):
        return time()
