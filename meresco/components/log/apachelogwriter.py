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

class ApacheLogWriter(object):
    def __init__(self, outputStream=None):
        self._out = outputStream

    def writeLog(self, **logItems):
        if self._out is None:
            return
        headers = getFirst(logItems, 'Headers', {})
        self._out.write(APACHE_LOGLINE.format(
                ipaddress=getFirst(logItems, 'Client', default=('-', 0))[0],
                user='-',
                timestamp=strftime('%d/%b/%Y:%H:%M:%S +0000', self._gmtime()),
                Method=getFirst(logItems, 'Method', '-'),
                pathAndQuery=stripToPathAndQuery(getFirst(logItems, 'RequestURI', '')),
                status=getFirst(logItems, 'responseHttpStatus', '0'),
                responseSize=getFirst(logItems, 'responseSize') or '-',
                Referer=headers.get('Referer', '-'),
                UserAgent=headers.get('User-Agent', '-'),
                HTTPVersion=getFirst(logItems, 'HTTPVersion', '1.0'),
            ))
        self._out.flush()

    def _gmtime(self):
        return gmtime()

def getFirst(aDict, key, default=None):
    return aDict.get(key, [default])[0]

def stripToPathAndQuery(requestUri):
    parsed = urlsplit(requestUri)
    result = parsed.path
    if parsed.query:
        result += '?' + parsed.query
    return result


APACHE_LOGLINE = '{ipaddress} - {user} [{timestamp}] "{Method} {pathAndQuery} HTTP/{HTTPVersion}" {status} {responseSize} "{Referer}" "{UserAgent}"\n'
