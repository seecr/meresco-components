## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014-2016, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from functools import total_ordering

@total_ordering
class Version(object):
    def __init__(self, versionString, majorDigits=2):
        self._versionString = '%s' % versionString
        if majorDigits < 1:
            raise ValueError("Use majorDigits >= 1")
        self._versionTuple = tuple(asint(p) for p in self._versionString.split('.'))
        self._majorVersionList = (list(self._versionTuple) + [0] * majorDigits)[:majorDigits]
        if X in self._majorVersionList:
            raise ValueError("'x' not allowed in majorVersion")
        self._nextMajorVersion = self._majorVersion = None

    @classmethod
    def create(cls, versionString, *args, **kwargs):
        if type(versionString) == cls:
            return versionString
        return cls(versionString)

    def __eq__(self, other):
        return self._versionTuple == other._versionTuple

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return self._versionTuple < other._versionTuple

    def __hash__(self):
        return hash(self.__class__) ^ hash(self._versionString)

    def majorVersion(self):
        if self._majorVersion is None:
            self._majorVersion = Version('.'.join(str(v) for v in self._majorVersionList), majorDigits=len(self._majorVersionList))
        return self._majorVersion

    def nextMajorVersion(self):
        if self._nextMajorVersion is None:
            nextMajorVersionList = self._majorVersionList[:-1] + [self._majorVersionList[-1] + 1]
            self._nextMajorVersion = Version('.'.join(str(v) for v in nextMajorVersionList), majorDigits=len(self._majorVersionList))
        return self._nextMajorVersion

    def __str__(self):
        return self._versionString

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, repr(self._versionString))

X = 99887766554433
def asint(aString):
    if aString == 'x':
        return X
    return int(aString)
