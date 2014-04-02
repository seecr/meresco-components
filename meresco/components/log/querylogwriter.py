## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2014 Stichting Kennisnet http://www.kennisnet.nl
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

from utils import getFirst, getScoped
from urllib import urlencode
from time import time

class QueryLogWriter(object):
    def __init__(self, log, scopeNames=None, argumentsSelection=dict(scope='sru', key='arguments')):
        self._log = log

        self._scopeNames = () if scopeNames is None else scopeNames

        self._scope = lambda name: self._scopeNames + (name,)
        self._argumentSelectionScope = argumentsSelection['scope']
        self._argumentSelectionKey = argumentsSelection['key']

    def writeLog(self, collectedLog):
        scopePresent = getScoped(collectedLog, self._scopeNames)
        if scopePresent is None:
            return
        httpRequest = getScoped(collectedLog, self._scope('httpRequest'), {})
        httpResponse = getScoped(collectedLog, self._scope('httpResponse'), {})
        sru = getScoped(collectedLog, self._scope('sru'), {})
        if not 'Client' in httpRequest:
            return

        path = getFirst(httpRequest, 'path')
        self._log.log(
            timestamp=getFirst(httpRequest, 'timestamp') or time(),
            path=path,
            ipAddress=getFirst(httpRequest, 'Client')[0],
            size=getFirst(httpResponse, 'size', 0)/1024.0,
            duration=getFirst(httpResponse, 'duration'),
            numberOfRecords=getFirst(sru, 'numberOfRecords'),
            queryArguments=self._queryArguments(collectedLog)
        )

    def _queryArguments(self, collectedLog):
        return sortedUrlEncode(getFirst(
                getScoped(collectedLog, self._scope(self._argumentSelectionScope), {}),
                key=self._argumentSelectionKey,
                default={}
            ))

    @classmethod
    def forHttpArguments(cls, log, **kwargs):
        return cls(log=log, argumentsSelection=dict(scope='httpRequest', key='arguments'))

def sortedUrlEncode(aDict):
    return str(urlencode(sorted(aDict.items()), doseq=True))