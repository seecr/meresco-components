## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Stichting Kennisnet https://www.kennisnet.nl
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

from urllib.request import Request, urlopen
from xml.sax.saxutils import escape as xmlEscape
from lxml.etree import XML

from weightless.http import httppost
from meresco.components.http.utils import CRLF, parseResponse
from meresco.xml.namespaces import xpathFirst


class SruUpdateClient(object):
    def __init__(self, host=None, port=None, path='/update', userAgent='SruUpdate', synchronous=False):
        self._host = host
        self._port = port
        self._path = path
        self._userAgent = userAgent
        self._synchronous = synchronous

    def updateHostAndPort(self, host, port):
        self._host = host
        self._port = port

    def add(self, identifier, data, **kwargs):
        yield self._upload(SRURECORDUPDATE_TEMPLATE % {
            b'recordIdentifier': bytes(xmlEscape(identifier), encoding="utf-8"),
            b'recordData': data if type(data) is bytes else bytes(data, encoding="utf-8")
        })

    def delete(self, identifier):
        yield self._upload(SRURECORDDELETE_TEMPLATE %  {
            b'recordIdentifier': bytes(xmlEscape(identifier), encoding="utf-8"),
        })

    def _upload(self, sruRecordUpdate):
        header, body = yield self._httppost(
            host=self._host,
            port=self._port,
            request=self._path,
            body=sruRecordUpdate,
            headers={'User-Agent': self._userAgent, 'Host': self._host}
        )

        url = "http://%s:%s%s" % (self._host, self._port, self._path)
        if header['StatusCode'] != '200':
            raise SruUpdateException(url=url, status=header['StatusCode'])
        response = XML(body)
        operationStatus = xpathFirst(response, "/srw:updateResponse/ucp:operationStatus/text()")
        if operationStatus != "success":
            raise SruUpdateException(
                url=url,
                status=operationStatus,
                diagnostics=xpathFirst(response, '//diag:diagnostic/diag:details/text()'))

    def _httppost(self, **kwargs):
        if self._synchronous:
            req = Request("http://%(host)s:%(port)s%(request)s" % kwargs, kwargs['body'])
            req.add_header('User-Agent', kwargs['headers']['User-Agent'])
            response = urlopen(req)
            return [dict(StatusCode=str(response.getcode())), response.read()]
        response = yield httppost(**kwargs)
        header, body = parseResponse(response)
        return [header, body]

class SruUpdateException(Exception):
    def __init__(self, url, status, diagnostics=None):
        self.url = url
        self.status = status
        self.diagnostics = diagnostics

    def __repr__(self):
        return "%s(%s, %s, %s)" % (self.__class__.__name__, self.url, self.status, self.diagnostics)

    def __str__(self):
        s = "SruUpdate to '%s' responded with status %s" % (self.url, self.status)
        if self.diagnostics:
            s += " and message '%s'" % self.diagnostics
        return s + "."


SRURECORDUPDATE_TEMPLATE = b"""<?xml version="1.0" encoding="UTF-8"?>
<ucp:updateRequest xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:action>info:srw/action/1/replace</ucp:action>
    <ucp:recordIdentifier>%(recordIdentifier)b</ucp:recordIdentifier>
    <srw:record>
        <srw:recordPacking>xml</srw:recordPacking>
        <srw:recordSchema>rdf</srw:recordSchema>
        <srw:recordData>%(recordData)b</srw:recordData>
    </srw:record>
</ucp:updateRequest>"""

SRURECORDDELETE_TEMPLATE = b"""<?xml version="1.0" encoding="UTF-8"?>
<ucp:updateRequest xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:action>info:srw/action/1/delete</ucp:action>
    <ucp:recordIdentifier>%(recordIdentifier)b</ucp:recordIdentifier>
    <srw:record>
        <srw:recordPacking>xml</srw:recordPacking>
        <srw:recordSchema>ignored</srw:recordSchema>
        <srw:recordData><ignored/></srw:recordData>
    </srw:record>
</ucp:updateRequest>"""
