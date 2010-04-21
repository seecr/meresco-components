## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
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

from cq2utils import CallTrace, CQ2TestCase

from meresco.components.sru.srurecordupdate import SRURecordUpdate
from amara.binderytools import bind_string


XML = """<?xml version="1.0" encoding="UTF-8"?>
<srw:updateRequest xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:action>info:srw/action/1/%(action)s</ucp:action>
    <ucp:recordIdentifier>%(recordIdentifier)s</ucp:recordIdentifier>
    <srw:record>
        <srw:recordPacking>%(recordPacking)s</srw:recordPacking>
        <srw:recordSchema>%(recordSchema)s</srw:recordSchema>
        <srw:recordData>%(recordData)s</srw:recordData>
    </srw:record>
</srw:updateRequest>"""

XML_DOCUMENT = """<someXml>
with strings<nodes and="attributes"/>
</someXml>"""

TEXT_DOCUMENT = """Just some text"""

CREATE = "create"
REPLACE = "replace"
DELETE = "delete"

class SRURecordUpdateTest(CQ2TestCase):
    """http://www.loc.gov/standards/sru/record-update/"""

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.sruRecordUpdate = SRURecordUpdate()
        self.observer = CallTrace("Observer")
        self.sruRecordUpdate.addObserver(self.observer)
        self.requestData = {
            "action": CREATE,
            "recordIdentifier": "defaultId",
            "recordPacking": "defaultPacking",
            "recordSchema": "defaultSchema",
            "recordData": "<defaultXml/>"
            }

    def createRequestBody(self, action=CREATE, recordData="<dc>empty</dc>"):
        return XML % {
            "action": action,
            "recordIdentifier": "123",
            "recordPacking": "text/xml",
            "recordSchema": "irrelevantXML",
            "recordData": recordData,
        }

    def performRequest(self, requestBody):
        result = ''.join(self.sruRecordUpdate.handleRequest(Body=requestBody))
        return result.split('\r\n\r\n')

    def testAddXML(self):
        requestBody = self.createRequestBody()
        headers, result = self.performRequest(requestBody)
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>success</ucp:operationStatus>
</srw:updateResponse>""", result)

        self.assertEquals(1, len(self.observer.calledMethods))
        method = self.observer.calledMethods[0]
        self.assertEquals(3, len(method.args))
        self.assertEquals("add", method.name)
        self.assertEquals("123", method.args[0])
        self.assertEquals(str, type(method.args[0]))
        self.assertEquals("irrelevantXML", method.args[1])
        self.assertEquals("<dc>empty</dc>", method.args[2].xml())

    def testDelete(self):
        requestBody = self.createRequestBody(action=DELETE)
        headers, result = self.performRequest(requestBody)
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>success</ucp:operationStatus>
</srw:updateResponse>""", result)
        self.assertEquals(1, len(self.observer.calledMethods))

        method = self.observer.calledMethods[0]
        self.assertEquals("delete", method.name)

    def testReplaceIsAdd(self):
        requestBody = self.createRequestBody(action=REPLACE)
        headers, result = self.performRequest(requestBody)
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>success</ucp:operationStatus>
</srw:updateResponse>""", result)
        self.assertEquals(1, len(self.observer.calledMethods))

        method = self.observer.calledMethods[0]
        self.assertEquals("add", method.name)

    def testNotCorrectXml(self):
        headers, result = self.performRequest("not_xml")
        self.assertTrue('<ucp:operationStatus>fail</ucp:operationStatus>' in result, result)
        self.assertEquals(0, len(self.observer.calledMethods))

    def testErrorsAreNotPassed(self):
        self.observer.exceptions['add'] = Exception('Some <Exception>')
        headers, result = self.performRequest(self.createRequestBody())
        self.assertTrue("""<ucp:operationStatus>fail</ucp:operationStatus>""" in result, result)
        diag = bind_string(result)
        self.assertTrue(str(diag.updateResponse.diagnostics.diagnostic.details).find("""Some <Exception>""") > -1)
