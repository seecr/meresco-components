## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2013-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from meresco.core import Transparent
from meresco.components import TimedDictionary
from weightless.io import TimeoutException
from time import time as now


class TimedMessageCache(Transparent):
    def __init__(self, cacheTimeout=1*60*60, returnCachedValueInCaseOfException=False, backoffTimeout=None, **kwargs):
        Transparent.__init__(self, **kwargs)
        self._cache = TimedDictionary(timeout=cacheTimeout)
        self._returnCachedValueInCaseOfException = returnCachedValueInCaseOfException
        self._backoffTimeout = backoffTimeout
        self._backoffStarted = None

    def clear(self):
        self._cache.clear()

    def setTimeout(self, timeout):
        self._cache.setTimeout(timeout)

    def getSize(self):
        return self._cache.size()

    def any_unknown(self, message, *args, **kwargs):
        found = False
        key = (message, repr(args), repr(kwargs))
        try:
            value = self._cache.peek(key)
        except KeyError:
            pass
        else:
            found = True
            if not self._cache.hasExpired(key):
                raise StopIteration(value)
        if self._backoffStarted:
            if self._backoffStarted + self._backoffTimeout < now():
                self._backoffStarted = None
            elif found:
                raise StopIteration(value)
            else:
                raise BackoffException()
        try:
            value = yield self.any.unknown(message, *args, **kwargs)
            self._cache[key] = value
        except (SystemExit, KeyboardInterrupt, AssertionError):
            raise
        except Exception, e:
            if self._backoffTimeout and isinstance(e, TimeoutException):
                self._backoffStarted = now()
                if not (self._returnCachedValueInCaseOfException and found):
                    raise BackoffException()
            if not (self._returnCachedValueInCaseOfException and found):
                raise
        raise StopIteration(value)
        yield

class BackoffException(Exception):
    pass
