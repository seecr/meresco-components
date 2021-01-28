## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014, 2016, 2018, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from time import gmtime, strftime
from urllib.parse import urlsplit
from .utils import getFirst, getScoped


class ApacheLogWriter(object):
    def __init__(self, outputStream=None, rejectLog=None):
        self._out = outputStream
        self._rejectLog = (lambda collectedLog: False) if rejectLog is None else rejectLog

    def writeLog(self, collectedLog):
        if self._out is None:
            return
        if self._rejectLog(collectedLog):
            return
        httpRequest = getScoped(collectedLog, scopeNames=(), key='httpRequest')
        httpResponse = getScoped(collectedLog, scopeNames=(), key='httpResponse')
        if not 'Client' in httpRequest:
            return
        headers = getFirst(httpRequest, 'Headers', {})
        template = APACHE_LOGLINE
        exception = getFirst(httpResponse, 'exception')
        if exception:
            template = ERROR_LOGLINE
        self._out.write(template.format(
            ipaddress=getFirst(httpRequest, key='Client', default=('-', 0))[0],
            user='-',
            timestamp=strftime('%d/%b/%Y:%H:%M:%S +0000', gmtime(getFirst(httpRequest, 'timestamp'))),
            Method=getFirst(httpRequest, 'Method', '-'),
            pathAndQuery=stripToPathAndQuery(getFirst(httpRequest, 'RequestURI', '')),
            status=getFirst(httpResponse, 'httpStatus', '0'),
            responseSize=getFirst(httpResponse, 'size') or '-',
            Referer=headers.get('Referer', '-'),
            UserAgent=headers.get('User-Agent', '-'),
            HTTPVersion=getFirst(httpRequest, 'HTTPVersion', '1.0'),
            Exception=None if not exception else repr(exception)
        ))
        self._out.flush()

def stripToPathAndQuery(requestUri):
    parsed = urlsplit(requestUri)
    result = parsed.path
    if parsed.query:
        result += '?' + parsed.query
    return result


LOGLINE = '{ipaddress} - {user} [{timestamp}] "{Method} {pathAndQuery} HTTP/{HTTPVersion}" {status} {responseSize} "{Referer}" "{UserAgent}"'
APACHE_LOGLINE = LOGLINE + '\n'
ERROR_LOGLINE = LOGLINE + " Exception raised:\n    {Exception}\n"
