## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.components.sru.diagnostic import UNSUPPORTED_PARAMETER_VALUE
from meresco.components.sru import SruException


class SruLimitStartRecord(Observable):
    def __init__(self, limitBeyond=1000, name=None):
        Observable.__init__(self, name=name)
        self._limitBeyond = limitBeyond

    def searchRetrieve(self, startRecord, maximumRecords, **kwargs):
        if startRecord > self._limitBeyond:
            raise SruException(UNSUPPORTED_PARAMETER_VALUE, "Argument 'startRecord' too high, maximum: %s" % self._limitBeyond)
        if startRecord + maximumRecords > self._limitBeyond + SRU_IS_ONE_BASED:
            raise SruException(UNSUPPORTED_PARAMETER_VALUE, "Argument 'startRecord' and 'maximumRecords' too high, maximum: %s" % self._limitBeyond)
        yield self.all.searchRetrieve(startRecord=startRecord, maximumRecords=maximumRecords, limitBeyond=self._limitBeyond, **kwargs)


SRU_IS_ONE_BASED = 1
