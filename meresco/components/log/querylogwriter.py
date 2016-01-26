## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2014, 2016 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from utils import getFirst, getScoped, scopePresent
from urllib import urlencode
from time import time
from meresco.core import Observable
from weightless.core import NoneOfTheObserversRespond

class QueryLogWriter(Observable):
    def __init__(self, log=None, scopeNames=None, argumentsSelection=dict(scope='sru', key='arguments'), **kwargs):
        Observable.__init__(self, **kwargs)
        self._log = self.call if log is None else log
        self._scopeNames = () if scopeNames is None else scopeNames
        self._argumentSelectionScope = argumentsSelection['scope']
        self._argumentSelectionKey = argumentsSelection['key']

    def writeLog(self, collectedLog):
        if not scopePresent(collectedLog, self._scopeNames):
            return
        httpRequest = getScoped(collectedLog, scopeNames=self._scopeNames, key='httpRequest')
        httpResponse = getScoped(collectedLog, scopeNames=self._scopeNames, key='httpResponse')
        sru = getScoped(collectedLog, scopeNames=self._scopeNames, key='sru')
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
            queryArguments=self._queryArguments(collectedLog),
            status=getFirst(httpResponse, 'httpStatus', '0'),
        )

    def _queryArguments(self, collectedLog):
        args = collectedLog
        if self._argumentSelectionScope is not None:
            args = getScoped(collectedLog, scopeNames=self._scopeNames, key=self._argumentSelectionScope)
        if self._argumentSelectionKey is not None:
            args = getFirst(
                args,
                key=self._argumentSelectionKey,
                default={}
            )
        try:
            args = self.call.determineQueryArguments(collectedLog=collectedLog, scopeNames=self._scopeNames, currentArgs=args)
        except NoneOfTheObserversRespond:
            pass
        return sortedUrlEncode(args)

    @classmethod
    def forHttpArguments(cls, log=None, **kwargs):
        return cls(log=log, argumentsSelection=dict(scope='httpRequest', key='arguments'), **kwargs)


def sortedUrlEncode(aDict):
    return str(urlencode(sorted(aDict.items()), doseq=True))