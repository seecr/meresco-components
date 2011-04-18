## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
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

from meresco.core import Transparant
from timeddictionary import TimedDictionary

class CacheComponent(Transparant):

    def __init__(self, timeout, methodName, keyKwarg):
        Transparant.__init__(self)
        self._methodName = methodName
        self._keyKwarg = keyKwarg
        self._cache = TimedDictionary(timeout=timeout)

    def unknown(self, method, *args, **kwargs):
        if self._methodName == method and self._keyKwarg in kwargs:
            keyValue = kwargs[self._keyKwarg]
            if not keyValue in self._cache:
                self._cache[keyValue] = self.any.unknown(method, *args, **kwargs)
            yield self._cache[keyValue]

        yield self.any.unknown(method, *args, **kwargs)
