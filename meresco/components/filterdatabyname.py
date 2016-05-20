## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2006-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2006-2012, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2011-2012, 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.core import Observable
from weightless.core import DeclineMessage

class FilterDataByName(Observable):
    def __init__(self, included=None, excluded=None):
        Observable.__init__(self)
        if included and excluded or not (included or excluded):
            raise ValueError("Use included OR excluded")
        if included:
            self._allowed = lambda name: name in included
        else:
            self._allowed = lambda name: not name in excluded

    def getData(self, identifier, name):
        if not self._allowed(name):
            raise DeclineMessage()
        result = yield self.any.getData(identifier=identifier, name=name)
        raise StopIteration(result)
