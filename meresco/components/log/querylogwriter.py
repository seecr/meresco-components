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

from utils import getFirst
from urllib import urlencode
from time import time
from logkeyvalue import LogKeyValue

class QueryLogWriter(object):
    ENABLE_LOG_KEY = 'queryLogWriterEnableLog'
    def __init__(self, log, checkLogEnabled=False, convertArgumentsMethod=None):
        self._log = log
        self._queryArguments = self.convertSruArguments if convertArgumentsMethod is None else convertArgumentsMethod
        self._checkLogEnabled = checkLogEnabled

    def writeLog(self, **logItems):
        if not 'Client' in logItems:
            return

        if self._checkLogEnabled:
            if not getFirst(logItems, self.ENABLE_LOG_KEY):
                return
        path=getFirst(logItems, 'path')
        self._log.log(
            timestamp=getFirst(logItems, 'timestamp') or time(),
            path=path,
            ipAddress=getFirst(logItems, 'Client')[0],
            size=getFirst(logItems, 'responseSize', 0)/1024.0,
            duration=getFirst(logItems, 'duration'),
            numberOfRecords=getFirst(logItems, 'sruNumberOfRecords'),
            queryArguments=self._queryArguments(**logItems)
        )

    @staticmethod
    def convertSruArguments(**logItems):
        return _queryArguments('sruArguments', **logItems)

    @staticmethod
    def convertArguments(**logItems):
        return _queryArguments('arguments', **logItems)

    @classmethod
    def enableLog(cls):
        return LogKeyValue({cls.ENABLE_LOG_KEY:True})

def _queryArguments(argumentsKey, **logItems):
    return sortedUrlEncode(**getFirst(logItems, argumentsKey, {}))

def sortedUrlEncode(**kwargs):
    return str(urlencode(sorted(kwargs.items()), doseq=True))