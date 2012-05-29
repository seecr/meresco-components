## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
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

from seecr.test import SeecrTestCase

from meresco.components.http.utils import CRLF
from meresco.components.http.httpclient import HttpClient

from weightless.core import compose

from lxml.etree import tostring

class HttpClientTest(SeecrTestCase):

    def sendAndReceive(self, gen, answer):
        shouldBeGenerator = str(gen.next())
        self.assertTrue(shouldBeGenerator.startswith("<generator object httpget at 0x"), shouldBeGenerator)
       
        try:
            gen.send(answer)
        except StopIteration, e:
            headers, body =  e.args[0]
        return headers, body

    def testPlainText(self):
        client = HttpClient()

        gen = client.httpGet(hostname='localhost', port=80, path='/', arguments={}, parse=False)
        headers, body = self.sendAndReceive(gen, """HTTP/1.0 200 Ok\r\nContent-Type: text/xml\r\n\r\n<xml/>""")

        self.assertEquals('<xml/>', body)
        self.assertEquals(['HTTP/1.0 200 Ok', 'Content-Type: text/xml'], headers.split(CRLF))
    
    def testPlainXml(self):
        client = HttpClient()

        gen = client.httpGet(hostname='localhost', port=80, path='/', arguments={})
        headers, body = self.sendAndReceive(gen,  """HTTP/1.0 200 Ok\r\nContent-Type: text/xml\r\n\r\n<xml/>""")
        
        self.assertEquals('<xml/>', tostring(body))
        self.assertEquals(['HTTP/1.0 200 Ok', 'Content-Type: text/xml'], headers.split(CRLF))
