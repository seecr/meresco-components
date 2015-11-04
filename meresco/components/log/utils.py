## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2014-2015 Stichting Kennisnet http://www.kennisnet.nl
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

from collections import namedtuple
import sys

def getFirst(aDict, key, default=None):
    return aDict.get(key, [default])[0]

_default = object()

def getScoped(aDict, scopeNames, key, default=_default):
    default = dict() if default is _default else default
    resultDict = aDict
    possibleAnswer = default
    for scopeName in scopeNames:
        possibleAnswer = resultDict.get(key, possibleAnswer)
        try:
            resultDict = resultDict[scopeName]
        except KeyError:
            break
    return resultDict.get(key, possibleAnswer)

def scopePresent(aDict, scopeNames):
    try:
        result = aDict
        for scopeName in scopeNames:
            result = result[scopeName]
        return True
    except KeyError:
        return False

DEFAULT_PARTS = ['timestamp', 'ipaddress', 'size', 'duration', 'hits', 'path', 'arguments']

class LogParse(object):
    def __init__(self, inputStream, parts=DEFAULT_PARTS):
        self.Line = namedtuple('Line', parts)
        self._partLength = len(parts)
        self._in = inputStream

    def lines(self):
        for line in self._in:
            parts = line.strip().split(' ') + [''] * self._partLength
            if any(parts):
                yield self.Line(*parts[:self._partLength])

    @classmethod
    def parse(cls, inputStreamOrFilename, **kwargs):
        if hasattr(inputStreamOrFilename, 'read'):
            inputStream = inputStreamOrFilename
        elif inputStreamOrFilename == '-':
            inputStream = sys.stdin
        else:
            inputStream = open(inputStreamOrFilename)
        return cls(inputStream, **kwargs)

