## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012, 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from seecr.test import SeecrTestCase

from meresco.components.http.utils import CRLF
from meresco.components.http import httpclient
from meresco.components.http.httpclient import HttpClient

from meresco.components import lxmltostring

from weightless.core import retval

class HttpClientTest(SeecrTestCase):

    def setUp(self):
        SeecrTestCase.setUp(self)
        def httpRequest(**kwargs):
            return self.response
            yield
        httpclient.httpget = httpRequest
        httpclient.httppost = httpRequest
        httpclient.httpsget = httpRequest
        httpclient.httpspost = httpRequest

    def testPlainText(self):
        client = HttpClient()
        self.response = b"""HTTP/1.0 200 OK\r\nContent-Type: text/xml\r\n\r\n<xml/>"""

        gen = client.httpGet(hostname='localhost', port=80, path='/', arguments={}, parse=False)
        headers, body = retval(gen)

        self.assertEqual('<xml/>', body)
        self.assertEqual(['HTTP/1.0 200 OK', 'Content-Type: text/xml'], headers.split(CRLF))

    def testPlainXml(self):
        client = HttpClient()
        self.response = b"""HTTP/1.0 200 OK\r\nContent-Type: text/xml\r\n\r\n<xml/>"""

        gen = client.httpGet(hostname='localhost', port=80, path='/', arguments={})
        headers, body = retval(gen)

        self.assertEqual('<xml/>', lxmltostring(body))
        self.assertEqual(['HTTP/1.0 200 OK', 'Content-Type: text/xml'], headers.split(CRLF))

    def testHttpPost(self):
        client = HttpClient()
        self.response = b"""HTTP/1.0 200 OK\r\n\r\nother-data"""

        gen = client.httpPost(hostname='localhost', port=80, path='/', data='data', parse=False)
        headers, body = retval(gen)

        self.assertEqual('other-data', body)
        self.assertEqual(['HTTP/1.0 200 OK'], headers.split(CRLF))

    def testHttpsGet(self):
        client = HttpClient()
        self.response = b"""HTTP/1.0 200 OK\r\n\r\nother-data"""

        gen = client.httpsGet(hostname='localhost', port=443, path='/', arguments={}, parse=False)
        headers, body = retval(gen)

        self.assertEqual('other-data', body)
        self.assertEqual(['HTTP/1.0 200 OK'], headers.split(CRLF))
