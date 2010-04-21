## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#    Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from meresco.core import Transparant
from time import strftime, gmtime
from urlparse import urlsplit

class DevNull(object):
    def write(self, *args, **kwargs):
        pass
    def flush(self, *args, **kwargs):
        pass

logline = '%(ipaddress)s - %(user)s [%(timestamp)s] "%(Method)s %(path)s%(query)s HTTP/1.0" %(status)s %(responseSize)s "%(Referer)s" "%(UserAgent)s"\n'
class ApacheLogger(Transparant):
    def __init__(self, outputStream=DevNull()):
        Transparant.__init__(self)
        self._outputStream = outputStream
        
    def handleRequest(self, *args, **kwargs):
        status = 0
        for line in self.all.handleRequest(*args, **kwargs):
            if not status and line.startswith('HTTP/1.0'):
                status = line[len('HTTP/1.0 '):][:3]
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
