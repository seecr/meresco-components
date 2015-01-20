# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2006-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2006-2012 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.core import Observable, Transparent
from weightless.core import compose

from time import time
from urllib.parse import urlencode

class QueryLog(Transparent):
    """
    Log incoming http queries with ip-address, path, size, timestamp, duration
    """

    def __init__(self, log, loggedPaths):
        Transparent.__init__(self)
        self._log = log
        self._loggedPaths = loggedPaths

    def handleRequest(self, Client, path, **kwargs):
        if not any(path.startswith(p) for p in self._loggedPaths):
            return self.all.handleRequest(Client=Client, path=path, **kwargs)
        return self._handleRequest(Client=Client, path=path, **kwargs)
        
    def _handleRequest(self, Client, path, **kwargs):
        _queryArguments = {}
        __callstack_var_queryLogValues__ = {'queryArguments':_queryArguments}

        timestamp = self._time()
        ipAddress = Client[0]
        sizeInBytes = 0
        for response in compose(self.all.handleRequest(Client=Client, path=path, **kwargs)):
            if hasattr(response, '__len__'):
                sizeInBytes += len(response)
            yield response
        size = sizeInBytes / 1024.0
        duration = self._time() - timestamp
        queryArguments = str(urlencode(sorted(_queryArguments.items()), doseq=True))
        numberOfRecords = __callstack_var_queryLogValues__.get('numberOfRecords', None)

        self._log.log(timestamp=timestamp,
            path=path,
            ipAddress=ipAddress,
            size=size,
            duration=duration,
            queryArguments=queryArguments,
            numberOfRecords=numberOfRecords)

    def _time(self):
        return time()


class QueryLogHelperForSru(Observable):
    def searchRetrieve(self, sruArguments, **kwargs):
        self.ctx.queryLogValues['queryArguments'].update(sruArguments)
        yield self.all.searchRetrieve(sruArguments=sruArguments, **kwargs)

class QueryLogHelper(Observable):
    def handleRequest(self, arguments, **kwargs):
        self.ctx.queryLogValues['queryArguments'].update(arguments)
        yield self.all.handleRequest(arguments=arguments, **kwargs)

class QueryLogHelperForExecuteCQL(Transparent):
    def executeQuery(self, **kwargs):
        response = yield self.any.executeQuery(**kwargs)
        self.ctx.queryLogValues['numberOfRecords'] = response.total
        raise StopIteration(response)

