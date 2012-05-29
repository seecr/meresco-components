from weightless.http import httpget
from meresco.components.http.utils import CRLF
from lxml.etree import parse as lxmlParse
from StringIO import StringIO
from urllib import urlencode

class HttpClient(object):

    def httpGetRequest(self, hostname, port, path, arguments, parse=True, **kwargs):
        response = yield httpget(hostname, port, '%s?%s' % (path, urlencode(arguments)))
        headers, body = response.split(CRLF*2)
        raise StopIteration((headers, lxmlParse(StringIO(body)) if parse else body))

