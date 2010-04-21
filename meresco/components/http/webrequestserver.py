## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from meresco.core import Observable
from weightless import HttpServer
from cgi import parse_qs
from urlparse import urlsplit
from StringIO import StringIO
from socket import gethostname

class WebRequest(object):
    def __init__(self, port=None, Client=None, RequestURI=None, Method=None, Headers=None, **kwargs):
        Scheme, Netloc, Path, Query, Fragment = urlsplit(RequestURI)
        self.stream = StringIO()
        self.write = self.stream.write
        self.path = Path
        self.method = Method
        self.uri = RequestURI
        self.args = parse_qs(Query)
        self.received_headers = Headers
        self.client = self
        self.host = Client[0]
        self.headers = Headers
        host = self
        host.port = port
        self.getHost = lambda: host
        self.headersOut = {}
        self.responseCode = 200
        if kwargs.has_key('Body'):
            self.content = StringIO(kwargs['Body'])

    def getRequestHostname(self):
        return self.headers.get('Host', gethostname()).split(':')[0]

    def setResponseCode(self, code):
        self.responseCode = code

    def setHeader(self, key, value):
        self.headersOut[key] = value

    def __str__(self):
        return '\t'.join((self.client.host, self.method, self.uri))

    def generateResponse(self):
        yield 'HTTP/1.0 %s Ok\r\n' % self.responseCode
        for key, value in self.headersOut.items():
            yield key.title() + ': ' + value + '\r\n'
        yield '\r\n'
        self.stream.seek(0)
        for line in self.stream.readlines():
            yield line

class WebRequestServer(Observable):

    def handleRequest(self,  **kwargs):
        webrequest = WebRequest(**kwargs)
        self.do.handleRequest(webrequest)
        return webrequest.generateResponse()
