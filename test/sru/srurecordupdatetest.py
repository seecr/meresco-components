## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#    Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
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

from cq2utils import CallTrace, CQ2TestCase

from meresco.components.sru.srurecordupdate import SRURecordUpdate
from amara.binderytools import bind_string
from weightless.core import compose
from meresco.components.xml_generic.validate import ValidateException


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

    def createRequestBody(self, action=CREATE, recordIdentifier="123", recordData="<dc>empty</dc>"):
        return XML % {
            "action": action,
            "recordIdentifier": recordIdentifier,
            "recordPacking": "text/xml",
            "recordSchema": "irrelevantXML",
            "recordData": recordData,
        }

    def performRequest(self, requestBody):
        result = ''.join(compose(self.sruRecordUpdate.handleRequest(Body=requestBody)))
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
        self.assertEquals(3, len(method.kwargs))
        self.assertEquals("add", method.name)
        self.assertEquals("123", method.kwargs['identifier'])
        self.assertEquals(str, type(method.kwargs['identifier']))
        self.assertEquals("irrelevantXML", method.kwargs['partname'])
        self.assertEquals("<dc>empty</dc>", method.kwargs['amaraNode'].xml())

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

    def testPassCallableObjectForAdd(self):
        def callable():
            pass
        self.observer.returnValues['add'] = (f for f in ['a', callable, 'b'])
        requestBody = self.createRequestBody(action=REPLACE)
        result = list(compose(self.sruRecordUpdate.handleRequest(Body=requestBody)))
        self.assertTrue(callable in result)
        result.remove(callable)
        header,body = (''.join(result)).split('\r\n\r\n')
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>success</ucp:operationStatus>
</srw:updateResponse>""", body)

    def testPassCallableObjectForDelete(self):
        def callable():
            pass
        self.observer.returnValues['delete'] = (f for f in ['a', callable, 'b'])
        requestBody = self.createRequestBody(action=DELETE)
        result = list(compose(self.sruRecordUpdate.handleRequest(Body=requestBody)))
        self.assertTrue(callable in result)
        result.remove(callable)
        header,body = (''.join(result)).split('\r\n\r\n')
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>success</ucp:operationStatus>
</srw:updateResponse>""", body)


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

    def testValidationErrors(self):
        self.observer.exceptions['add'] = ValidateException('Some <Exception>')
        headers, result = self.performRequest(self.createRequestBody())
        self.assertTrue("""<ucp:operationStatus>fail</ucp:operationStatus>""" in result, result)
        diag = bind_string(result)
        self.assertEquals("info:srw/diagnostic/12/12", str(diag.updateResponse.diagnostics.diagnostic.uri))
        self.assertEquals("Some <Exception>", str(diag.updateResponse.diagnostics.diagnostic.details))
        self.assertEquals("Invalid data:  record rejected", str(diag.updateResponse.diagnostics.diagnostic.message))

    def testEmptyIdentifierNotAccepted(self):
        requestBody = self.createRequestBody(recordIdentifier="")
        headers, result = self.performRequest(requestBody)
        self.assertTrue("""<ucp:operationStatus>fail</ucp:operationStatus>""" in result, result)
        diag = bind_string(result)
        self.assertEquals("info:srw/diagnostic/12/1", str(diag.updateResponse.diagnostics.diagnostic.uri))
        self.assertTrue("Empty recordIdentifier not allowed." in str(diag.updateResponse.diagnostics.diagnostic.details))
        self.assertEquals("Invalid component:  record rejected", str(diag.updateResponse.diagnostics.diagnostic.message))

    def testNoIdentifierNotAccepted(self):
        requestBody = """<?xml version="1.0" encoding="UTF-8"?>
<srw:updateRequest xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:action>info:srw/action/1/%(action)s</ucp:action>
    <srw:record>
        <srw:recordPacking>xml</srw:recordPacking>
        <srw:recordSchema>ascheme</srw:recordSchema>
        <srw:recordData>some data</srw:recordData>
    </srw:record>
</srw:updateRequest>"""
        headers, result = self.performRequest(requestBody)
        self.assertTrue("""<ucp:operationStatus>fail</ucp:operationStatus>""" in result, result)
        diag = bind_string(result)
        self.assertEquals("info:srw/diagnostic/12/1", str(diag.updateResponse.diagnostics.diagnostic.uri))
        self.assertTrue("no attribute \'recordIdentifier\'" in str(diag.updateResponse.diagnostics.diagnostic.details))
        self.assertEquals("Invalid component:  record rejected", str(diag.updateResponse.diagnostics.diagnostic.message))

