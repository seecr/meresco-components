from seecr.test import SeecrTestCase

from meresco.components.http.utils import CRLF
from meresco.components.http.httpclient import HttpClient

from weightless.core import compose

class HttpClientTest(SeecrTestCase):
    def testOne(self):
        client = HttpClient()

        x = client.httpGetRequest(hostname='localhost', port=80, path='/', arguments={}, parse=False)
        xx = str(x.next())
        self.assertTrue(xx.startswith("<generator object httpget at 0x"), xx)
       
        try:
            x.send("HTTP/1.0 200 Ok\r\nContent-Type: text/xml\r\n\r\n<xml/>")
        except StopIteration, e:
            headers, body =  e.args[0]
        
        self.assertEquals('<xml/>', body)
        self.assertEquals(['HTTP/1.0 200 Ok', 'Content-Type: text/xml'], headers.split(CRLF))
