## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2013, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from weightless.core import compose
from meresco.components.sru.sruupdateclient import SruUpdateClient, SruUpdateException


class SruUpdateClientTest(SeecrTestCase):
    def testAddSuccess(self):
        postArguments = []
        def _httppost(**kwargs):
            postArguments.append(kwargs)
            return [
                dict(StatusCode="200"),
                SRU_UPDATE_RESPONSE % (b"success", b'')
            ]
            yield
        sruUpdate = SruUpdateClient(host='localhost', port=1234, userAgent="testAgent")
        sruUpdate._httppost = _httppost
        list(compose(sruUpdate.add(identifier='anIdentifier', data=b'<xml/>')))
        self.assertEqual(1, len(postArguments))
        arguments = postArguments[0]
        self.assertEqual('localhost', arguments['host'])
        self.assertEqual(1234, arguments['port'])
        self.assertEqual('/update', arguments['request'])
        self.assertEqual({"User-Agent": "testAgent", "Host": 'localhost'}, arguments['headers'])
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
            <ucp:updateRequest xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
            <srw:version>1.0</srw:version>
            <ucp:action>info:srw/action/1/replace</ucp:action>
            <ucp:recordIdentifier>anIdentifier</ucp:recordIdentifier>
            <srw:record>
                <srw:recordPacking>xml</srw:recordPacking>
                <srw:recordSchema>rdf</srw:recordSchema>
                <srw:recordData><xml/></srw:recordData>
            </srw:record>
        </ucp:updateRequest>""", str(arguments['body'], encoding="utf-8"))
    
    def testAddSuccessDataIsNotBytes(self):
        postArguments = []
        def _httppost(**kwargs):
            postArguments.append(kwargs)
            return [
                dict(StatusCode="200"),
                str(SRU_UPDATE_RESPONSE % (b"success", b''), encoding="utf-8")
            ]
            yield
        sruUpdate = SruUpdateClient(host='localhost', port=1234, userAgent="testAgent")
        sruUpdate._httppost = _httppost
        list(compose(sruUpdate.add(identifier='anIdentifier', data=b'<xml/>')))
        self.assertEqual(1, len(postArguments))
        arguments = postArguments[0]
        self.assertEqual('localhost', arguments['host'])
        self.assertEqual(1234, arguments['port'])
        self.assertEqual('/update', arguments['request'])
        self.assertEqual({"User-Agent": "testAgent", "Host": 'localhost'}, arguments['headers'])
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
            <ucp:updateRequest xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
            <srw:version>1.0</srw:version>
            <ucp:action>info:srw/action/1/replace</ucp:action>
            <ucp:recordIdentifier>anIdentifier</ucp:recordIdentifier>
            <srw:record>
                <srw:recordPacking>xml</srw:recordPacking>
                <srw:recordSchema>rdf</srw:recordSchema>
                <srw:recordData><xml/></srw:recordData>
            </srw:record>
        </ucp:updateRequest>""", str(arguments['body'], encoding="utf-8"))

    def testAddFailed(self):
        postArguments = []
        def _httppost(**kwargs):
            postArguments.append(kwargs)
            return [
                dict(StatusCode="200"),
                SRU_UPDATE_RESPONSE % (b"fail", SRU_DIAGNOSTICS)
            ]
            yield
        sruUpdate = SruUpdateClient()
        sruUpdate._httppost = _httppost
        sruUpdate.updateHostAndPort('localhost', 12345)
        try:
            list(compose(sruUpdate.add(identifier='anIdentifier', data=b'<xml/>')))
            self.fail("should not get here")
        except SruUpdateException as e:
            self.assertEqual(e.url, 'http://localhost:12345/update')
            self.assertEqual(e.status, 'fail')
            self.assertEqual(e.diagnostics, 'Traceback: some traceback')

    def testDelete(self):
        postArguments = []
        def _httppost(**kwargs):
            postArguments.append(kwargs)
            return [
                dict(StatusCode="200"),
                SRU_UPDATE_RESPONSE % (b"success", b'')
            ]
            yield
        sruUpdate = SruUpdateClient(host='localhost', port=1234, userAgent="testAgent")
        sruUpdate._httppost = _httppost
        list(compose(sruUpdate.delete(identifier='anIdentifier')))
        self.assertEqual(1, len(postArguments))
        arguments = postArguments[0]
        self.assertEqual('localhost', arguments['host'])
        self.assertEqual(1234, arguments['port'])
        self.assertEqual('/update', arguments['request'])
        self.assertEqual({"User-Agent": "testAgent", "Host": 'localhost'}, arguments['headers'])
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
            <ucp:updateRequest xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
            <srw:version>1.0</srw:version>
            <ucp:action>info:srw/action/1/delete</ucp:action>
            <ucp:recordIdentifier>anIdentifier</ucp:recordIdentifier>
            <srw:record>
                <srw:recordPacking>xml</srw:recordPacking>
                <srw:recordSchema>ignored</srw:recordSchema>
                <srw:recordData><ignored/></srw:recordData>
            </srw:record>
        </ucp:updateRequest>""", str(arguments['body'], encoding="utf-8"))


SRU_UPDATE_RESPONSE = b"""
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>%b</ucp:operationStatus>%b
</srw:updateResponse>
"""

SRU_DIAGNOSTICS = b"""<srw:diagnostics>
    <diag:diagnostic xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/">
        <diag:uri>info:srw/diagnostic/12/1</diag:uri>
        <diag:details>Traceback: some traceback</diag:details>
        <diag:message>Invalid component:  record rejected</diag:message>
    </diag:diagnostic>
</srw:diagnostics>"""
