## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012-2013, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from weightless.http import httpget, httppost, httpspost, httpsget
from meresco.components.http.utils import CRLF
from lxml.etree import parse as lxmlParse
from io import BytesIO
from urllib.parse import urlencode

class HttpClient(object):

    def httpGet(self, hostname, port, path, arguments, parse=True, **kwargs):
        return (
            yield _doRequest(httpget, parse=parse, host=hostname, port=port, request='%s?%s' % (path, urlencode(arguments)), **kwargs)
        )

    def httpsGet(self, hostname, port, path, arguments, parse=True, **kwargs):
        return (
            yield _doRequest(httpsget, parse=parse, host=hostname, port=port, request='%s?%s' % (path, urlencode(arguments)), **kwargs)
        )

    def httpPost(self, hostname, port, path, data, parse=True, **kwargs):
        return (
            yield _doRequest(httppost, parse=parse, host=hostname, port=port, request=path, body=data, **kwargs)
        )

    def httpsPost(self, hostname, port, path, data, parse=True, **kwargs):
        return (
            yield _doRequest(httpspost, parse=parse, host=hostname, port=port, request=path, body=data, **kwargs)
        )

def _doRequest(method, parse, **kwargs):
    response = yield method(**kwargs)
    headers, body = response.split(b'\r\n\r\n')
    return (headers.decode(), lxmlParse(BytesIO(body)) if parse else body.decode())
