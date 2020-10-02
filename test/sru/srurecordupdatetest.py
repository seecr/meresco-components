## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010-2011, 2014, 2018 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012-2014, 2018 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from seecr.test import SeecrTestCase, CallTrace

from meresco.components.sru.srurecordupdate import SruRecordUpdate
from meresco.components import lxmltostring
from lxml.etree import parse, XML, _ElementTree as ElementTreeType
from meresco.xml.namespaces import xpathFirst
from io import StringIO
from weightless.core import compose
from meresco.components.xml_generic.validate import ValidateException
from meresco.core import asyncnoreturnvalue
from collections import defaultdict


UPDATE_REQUEST = """<?xml version="1.0" encoding="UTF-8"?>
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

class SruRecordUpdateTest(SeecrTestCase):
    """http://www.loc.gov/standards/sru/record-update/"""

    def setUp(self):
        SeecrTestCase.setUp(self)
        self.stderr = StringIO()
        self.initSruRecordUpdate(stderr=self.stderr, logErrors=True, enableCollectLog=True)

    def initSruRecordUpdate(self, **kwargs):
        self.sruRecordUpdate = SruRecordUpdate(**kwargs)
        self.observer = CallTrace("Observer", emptyGeneratorMethods=['add', 'delete', 'deleteRecord'])
        self.sruRecordUpdate.addObserver(self.observer)

    def createRequestBody(self, action=CREATE, recordIdentifier="123", recordData="<dc>empty</dc>"):
        return UPDATE_REQUEST% {
            "action": action,
            "recordIdentifier": recordIdentifier,
            "recordPacking": "text/xml",
            "recordSchema": "irrelevantXML",
            "recordData": recordData,
        }

    def performRequest(self, requestBody):
        __callstack_var_logCollector__ = self.logCollector = dict()
        result = ''.join(compose(self.sruRecordUpdate.handleRequest(Body=requestBody)))
        return result.split('\r\n\r\n')

    def testAddXML(self):
        requestBody = self.createRequestBody(recordData='<my:data xmlns:my="mine">data</my:data>      ')
        headers, result = self.performRequest(requestBody)
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>success</ucp:operationStatus>
</srw:updateResponse>""", result)

        self.assertEqual(1, len(self.observer.calledMethods))
        method = self.observer.calledMethods[0]
        self.assertEqual(3, len(method.kwargs))
        self.assertEqual("add", method.name)
        self.assertEqual("123", method.kwargs['identifier'])
        self.assertEqual(str, type(method.kwargs['identifier']))
        self.assertEqual("irrelevantXML", method.kwargs['partname'])
        resultNode = method.kwargs['lxmlNode']
        self.assertEqualsLxml(XML('<my:data xmlns:my="mine">data</my:data>'), resultNode)
        self.assertEqual(['data'], resultNode.xpath('/my:data/text()', namespaces={'my':'mine'}))
        self.assertEqual(ElementTreeType, type(resultNode))
        self.assertEqual(None, resultNode.getroot().tail)

    def testWithoutLogging(self):
        self.sruRecordUpdate = SruRecordUpdate(stderr=self.stderr, logErrors=True, enableCollectLog=False)
        self.sruRecordUpdate.addObserver(self.observer)
        requestBody = self.createRequestBody(recordData='<my:data xmlns:my="mine">data</my:data>      ')
        headers, result = self.performRequest(requestBody)
        self.assertTrue('<ucp:operationStatus>success</ucp:operationStatus>' in result)
        self.assertEqual(dict(), self.logCollector)

    def testDelete(self):
        requestBody = self.createRequestBody(action=DELETE)
        headers, result = self.performRequest(requestBody)
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>success</ucp:operationStatus>
</srw:updateResponse>""", result)
        self.assertEqual(1, len(self.observer.calledMethods))

        method = self.observer.calledMethods[0]
        self.assertEqual("delete", method.name)

    def testReplaceIsAdd(self):
        requestBody = self.createRequestBody(action=REPLACE)
        headers, result = self.performRequest(requestBody)
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>success</ucp:operationStatus>
</srw:updateResponse>""", result)
        self.assertEqual(1, len(self.observer.calledMethods))

        method = self.observer.calledMethods[0]
        self.assertEqual("add", method.name)

    def testDeleteRecord(self):
        self.initSruRecordUpdate(stderr=self.stderr, logErrors=True, enableCollectLog=True, supportDeleteRecord=True)
        requestBody = self.createRequestBody(action=DELETE)
        headers, result = self.performRequest(requestBody)
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>success</ucp:operationStatus>
</srw:updateResponse>""", result)
        self.assertEqual(1, len(self.observer.calledMethods))

        method = self.observer.calledMethods[0]
        self.assertEqual("deleteRecord", method.name)
        self.assertEqual('123', method.kwargs['identifier'])
        self.assertEqualsWS('''<srw:record xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
        <srw:recordPacking>text/xml</srw:recordPacking>
        <srw:recordSchema>irrelevantXML</srw:recordSchema>
        <srw:recordData><dc>empty</dc></srw:recordData>
</srw:record>''', lxmltostring(method.kwargs['record']))

    def testAddXMLWithUcpUpdateRequest(self):
        """It is not entirely sure if updateRequest is in the 'srw' or 'ucp' namespace.
        We now assume it is in 'srw', but versions of meresco-harvester use 'ucp'.
        We will accept both.
        """
        requestBody = self.createRequestBody()
        requestBody = requestBody.replace('srw:updateRequest', 'ucp:updateRequest')
        headers, result = self.performRequest(requestBody)
        self.assertEqualsWS("""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>success</ucp:operationStatus>
</srw:updateResponse>""", result)

        self.assertEqual(['add'], self.observer.calledMethodNames())

    def testPassCallableObjectForAdd(self):
        def callable():
            pass
        self.observer.returnValues['add'] = (f for f in [callable])
        requestBody = self.createRequestBody(action=REPLACE)
        __callstack_var_logCollector__ = defaultdict(list)
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
        self.observer.returnValues['delete'] = (f for f in [callable])
        requestBody = self.createRequestBody(action=DELETE)
        __callstack_var_logCollector__ = defaultdict(list)
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
        self.assertEqual(0, len(self.observer.calledMethods))
        self.assertTrue('XMLSyntaxError' in self.stderr.getvalue(), self.stderr.getvalue())

    def testErrorsAreNotPassed(self):
        self.observer.exceptions['add'] = Exception('Some <Exception>')
        headers, result = self.performRequest(self.createRequestBody())
        self.assertTrue("""<ucp:operationStatus>fail</ucp:operationStatus>""" in result, result)
        diag = parse(StringIO(result))
        self.assertTrue("Some <Exception>" in xpathFirst(diag, '/srw:updateResponse/srw:diagnostics/diag:diagnostic/diag:details/text()'), result)

    def testValidationErrors(self):
        self.observer.exceptions['add'] = ValidateException('Some <Exception>')
        headers, result = self.performRequest(self.createRequestBody())
        self.assertTrue("""<ucp:operationStatus>fail</ucp:operationStatus>""" in result, result)
        diag = parse(StringIO(result))
        self.assertEqual("info:srw/diagnostic/12/12", xpathFirst(diag, '/srw:updateResponse/srw:diagnostics/diag:diagnostic/diag:uri/text()'))
        self.assertEqual("Some <Exception>", xpathFirst(diag, '/srw:updateResponse/srw:diagnostics/diag:diagnostic/diag:details/text()'))
        self.assertEqual("Invalid data:  record rejected", xpathFirst(diag, '/srw:updateResponse/srw:diagnostics/diag:diagnostic/diag:message/text()'))

    def testEmptyIdentifierNotAccepted(self):
        requestBody = self.createRequestBody(recordIdentifier="")
        headers, result = self.performRequest(requestBody)
        self.assertTrue("""<ucp:operationStatus>fail</ucp:operationStatus>""" in result, result)
        diag = parse(StringIO(result))
        self.assertEqual("info:srw/diagnostic/12/1", xpathFirst(diag, '/srw:updateResponse/srw:diagnostics/diag:diagnostic/diag:uri/text()'))
        self.assertTrue("recordIdentifier is mandatory." in xpathFirst(diag, '/srw:updateResponse/srw:diagnostics/diag:diagnostic/diag:details/text()'), result)
        self.assertTrue("Invalid component:  record rejected" in xpathFirst(diag, '/srw:updateResponse/srw:diagnostics/diag:diagnostic/diag:message/text()'), result)

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
        diag = parse(StringIO(result))
        self.assertEqual("info:srw/diagnostic/12/1", xpathFirst(diag, '/srw:updateResponse/srw:diagnostics/diag:diagnostic/diag:uri/text()'))
        self.assertTrue("recordIdentifier is mandatory." in xpathFirst(diag, '/srw:updateResponse/srw:diagnostics/diag:diagnostic/diag:details/text()'), result)
        self.assertEqual("Invalid component:  record rejected", xpathFirst(diag, '/srw:updateResponse/srw:diagnostics/diag:diagnostic/diag:message/text()'))

    def testCollectLog(self):
        requestBody = self.createRequestBody(action=DELETE, recordIdentifier='idDelete')
        headers, result = self.performRequest(requestBody)
        self.assertEqual(dict(sruRecordUpdate=dict(delete=['idDelete'])), self.logCollector)
        requestBody = self.createRequestBody(action=CREATE, recordIdentifier='idAdd')
        headers, result = self.performRequest(requestBody)
        self.assertEqual(dict(sruRecordUpdate=dict(add=['idAdd'])), self.logCollector)

    def testCollectLogWithErrors(self):
        self.observer.exceptions['delete'] = Exception('Some <Exception>')
        requestBody = self.createRequestBody(action=DELETE, recordIdentifier='idDelete')
        headers, result = self.performRequest(requestBody)
        self.assertEqual(dict(
            sruRecordUpdate=dict(
                delete=['idDelete'],
                errorType=['Exception'],
                errorMessage=["Some <Exception>"]
            )), self.logCollector)

        self.observer.exceptions['add'] = ValidateException('Nee')
        requestBody = self.createRequestBody(action=CREATE, recordIdentifier='idAdd')
        headers, result = self.performRequest(requestBody)
        self.assertEqual(dict(
            sruRecordUpdate=dict(
                add=['idAdd'],
                invalid=['idAdd'],
                errorType=['ValidateException'],
                errorMessage=["Nee"]
            )), self.logCollector)

        headers, result = self.performRequest('<srw:updateRequest>Will raise XMLSyntaxError')
        sru_error = self.logCollector['sruRecordUpdate']
        self.assertEqual(['XMLSyntaxError'], sru_error['errorType'])
        self.assertTrue(sru_error['errorMessage'][0].startswith('Namespace prefix srw on updateRequest is not defined, line 1, column 19'))

