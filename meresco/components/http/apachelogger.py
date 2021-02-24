## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
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

from meresco.core import Transparent
from weightless.core import compose, Yield
from time import strftime, gmtime
from urllib.parse import urlsplit

class DevNull(object):
    def write(self, *args, **kwargs):
        pass
    def flush(self, *args, **kwargs):
        pass

logline = '%(ipaddress)s - %(user)s [%(timestamp)s] "%(Method)s %(path)s%(query)s HTTP/1.0" %(status)s %(responseSize)s "%(Referer)s" "%(UserAgent)s"\n'
class ApacheLogger(Transparent):
    def __init__(self, outputStream=DevNull()):
        Transparent.__init__(self)
        self._outputStream = outputStream

    def handleRequest(self, *args, **kwargs):
        status = 0
        for line in compose(self.all.handleRequest(*args, **kwargs)):
            if line is Yield or callable(line):
                yield line
                continue
            if not status and asBytes(line).startswith(b'HTTP/1.'):
                status = str(asBytes(line)[len(b'HTTP/1.0 '):][:3], encoding='utf-8')
                self._log(status, **kwargs)
            yield line

    def logHttpError(self, ResponseCode, RequestURI, *args, **kwargs):
        scheme, netloc, path, query, fragments = urlsplit(RequestURI)
        self._log(ResponseCode, path=path, query=query, **kwargs)
        self.do.logHttpError(ResponseCode=ResponseCode, RequestURI=RequestURI, **kwargs)

    def _log(self, status, Method, Client, query, Headers, path,  **kwargs):
        ipaddress = Client[0]
        timestamp = strftime('%d/%b/%Y:%H:%M:%S +0000', gmtime())
        responseSize = '??'
        user = '-'
        query = query and '?%s' % query or ''
        Referer = Headers.get('Referer', '-')
        UserAgent = Headers.get('User-Agent', '-')

        self._outputStream.write(logline % locals())
        self._outputStream.flush()

def asBytes(s):
    if type(s) is str:
        return bytes(s, encoding='utf-8')
    return s
