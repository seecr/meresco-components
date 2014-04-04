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
from time import gmtime, strftime
from urlparse import urlsplit
from utils import getFirst, getScoped

class ApacheLogWriter(object):
    def __init__(self, outputStream=None):
        self._out = outputStream

    def writeLog(self, collectedLog):
        if self._out is None:
            return
        httpRequest = getScoped(collectedLog, ('httpRequest',))
        httpResponse = getScoped(collectedLog, ('httpResponse',))
        if not 'Client' in httpRequest:
            return
        headers = getFirst(httpRequest, 'Headers', {})
        self._out.write(APACHE_LOGLINE.format(
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
            ))
        self._out.flush()

def stripToPathAndQuery(requestUri):
    parsed = urlsplit(requestUri)
    result = parsed.path
    if parsed.query:
        result += '?' + parsed.query
    return result


APACHE_LOGLINE = '{ipaddress} - {user} [{timestamp}] "{Method} {pathAndQuery} HTTP/{HTTPVersion}" {status} {responseSize} "{Referer}" "{UserAgent}"\n'
