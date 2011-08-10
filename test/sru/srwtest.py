## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

from cq2utils import CQ2TestCase, CallTrace

from meresco.components.sru import SruHandler, SruParser
from meresco.components.sru.srw import Srw

httpResponse = """HTTP/1.0 200 OK
Content-Type: text/xml; charset=utf-8

%s"""

soapEnvelope = """<SOAP:Envelope xmlns:SOAP="http://schemas.xmlsoap.org/soap/envelope/"><SOAP:Body>%s</SOAP:Body></SOAP:Envelope>"""

echoedSearchRetrieveRequest = """<srw:echoedSearchRetrieveRequest>
<srw:version>1.1</srw:version>
<srw:query>%s</srw:query>
<srw:startRecord>1</srw:startRecord>
<srw:maximumRecords>10</srw:maximumRecords>
<srw:recordPacking>xml</srw:recordPacking>
<srw:recordSchema>dc</srw:recordSchema>
</srw:echoedSearchRetrieveRequest>"""

searchRetrieveResponse = """<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/">\n<srw:version>1.1</srw:version><srw:numberOfRecords>%i</srw:numberOfRecords>%s</srw:searchRetrieveResponse>"""

wrappedMockAnswer = searchRetrieveResponse % (1, '<srw:records><srw:record><srw:recordSchema>dc</srw:recordSchema><srw:recordPacking>xml</srw:recordPacking><srw:recordData><DATA>%s-dc</DATA></srw:recordData></srw:record></srw:records>' + echoedSearchRetrieveRequest)

SRW_REQUEST = """<SRW:searchRetrieveRequest xmlns:SRW="http://www.loc.gov/zing/srw/">%s</SRW:searchRetrieveRequest>"""

argumentsWithMandatory = """<SRW:version>1.1</SRW:version><SRW:query>dc.author = "jones" and  dc.title = "smith"</SRW:query>%s"""

class SrwTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.srw = Srw()
        self.sruParser = SruParser()
        self.sruHandler = SruHandler()
        
        self.srw.addObserver(self.sruParser)
        self.sruParser.addObserver(self.sruHandler)


    def testNonSoap(self):
        """Wrong Soap envelope or body"""
        invalidSoapEnvelope = '<?xml version="1.0"?><SOAP:Envelope xmlns:SOAP="http://wrong.example.org/soap/envelope/"><SOAP:Body>%s</SOAP:Body></SOAP:Envelope>'
        request = invalidSoapEnvelope % SRW_REQUEST % argumentsWithMandatory % ""

        response = "".join(list(Srw().handleRequest(Body=request)))
        self.assertEqualsWS("""HTTP/1.0 500 Internal Server Error
Content-Type: text/xml; charset=utf-8

<SOAP:Envelope xmlns:SOAP="http://schemas.xmlsoap.org/soap/envelope/"><SOAP:Body><SOAP:Fault><faultcode>SOAP:VersionMismatch</faultcode><faultstring>The processing party found an invalid namespace for the SOAP Envelope element</faultstring></SOAP:Fault></SOAP:Body></SOAP:Envelope>""", response)

    def testMalformedXML(self):
        """Stuff that is not even XML"""
        request = 'This is not even XML'

        response = "".join(self.srw.handleRequest(Body=request))
        self.assertTrue('<faultcode>SOAP:Server.userException</faultcode>' in response)

    def testNonSRUArguments(self):
        """Arguments that are invalid in any SRU implementation"""
        request =  soapEnvelope % SRW_REQUEST % argumentsWithMandatory % """<SRW:illegalParameter>value</SRW:illegalParameter>"""

        response = "".join(self.srw.handleRequest(Body=request))

        self.assertEqualsWS(httpResponse % soapEnvelope % """<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<srw:version>1.1</srw:version><srw:numberOfRecords>0</srw:numberOfRecords><srw:diagnostics><diagnostic xmlns="http://www.loc.gov/zing/srw/diagnostic/">
        <uri>info://srw/diagnostics/1/8</uri>
        <details>illegalParameter</details>
        <message>Unsupported Parameter</message>
    </diagnostic></srw:diagnostics></srw:searchRetrieveResponse>""", response)

    def testNonSRWArguments(self):
        """Arguments that are part of SRU, but not of SRW (operation (done), stylesheet)
        """
        request =  soapEnvelope % SRW_REQUEST % argumentsWithMandatory % """<SRW:stylesheet>http://example.org/style.xsl</SRW:stylesheet>"""

        response = "".join(self.srw.handleRequest(Body=request))

        self.assertEqualsWS(httpResponse % soapEnvelope % """<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<srw:version>1.1</srw:version><srw:numberOfRecords>0</srw:numberOfRecords><srw:diagnostics><diagnostic xmlns="http://www.loc.gov/zing/srw/diagnostic/">
        <uri>info://srw/diagnostics/1/8</uri>
        <details>stylesheet</details>
        <message>Unsupported Parameter</message>
    </diagnostic></srw:diagnostics></srw:searchRetrieveResponse>""", response)


    def testOperationIsIllegal(self):
        request = soapEnvelope % SRW_REQUEST % """<SRW:version>1.1</SRW:version><SRW:operation>explain</SRW:operation>"""

        response = "".join(self.srw.handleRequest(Body=request))

        self.assertEqualsWS(httpResponse % soapEnvelope % """<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<srw:version>1.1</srw:version><srw:numberOfRecords>0</srw:numberOfRecords><srw:diagnostics><diagnostic xmlns="http://www.loc.gov/zing/srw/diagnostic/">
        <uri>info://srw/diagnostics/1/4</uri>
        <details>explain</details>
        <message>Unsupported Operation</message>
    </diagnostic></srw:diagnostics></srw:searchRetrieveResponse>""", response)

    def testContentType(self):
        observer = CallTrace(
            returnValues={'executeCQL': (1, [0])},
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData', 'yieldRecord'])
        self.sruHandler.addObserver(observer)

        request = soapEnvelope % SRW_REQUEST % argumentsWithMandatory % ''
        response = "".join(self.srw.handleRequest(Body=request))
        self.assertTrue('text/xml; charset=utf-8' in response, response)

    def testNormalOperation(self):
        request = soapEnvelope % SRW_REQUEST % argumentsWithMandatory % ""
        observer = CallTrace(
            returnValues={
                'executeCQL': (1, ['recordId']),
            },
            methods={
                'yieldRecord': lambda identifier, partname: (g for g in ["<DATA>%s-%s</DATA>" % (identifier, partname)])
            },
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])

        self.sruHandler.addObserver(observer)

        result = "".join(self.srw.handleRequest(Body=request))

        self.assertEqualsWS(httpResponse % soapEnvelope % wrappedMockAnswer % ('recordId', 'dc.author = "jones" and  dc.title = "smith"'), result)

    def testArgumentsAreNotUnicodeStrings(self):
        """JJ/TJ: unicode strings somehow paralyse server requests.
        So ensure every argument is a str!"""
        """KvS d.d. 2007/11/15 - is this true in the Component-context too?"""
        request = soapEnvelope % SRW_REQUEST % argumentsWithMandatory % ""
        component = Srw()
        arguments = component._soapXmlToArguments(request)
        for key in arguments:
            self.assertTrue(type(key) == str)

    def testExampleFromLibraryOffCongressSite(self):
        """testExampleFromLibraryOffCongressSite - Integration test based on http://www.loc.gov/standards/sru/srw/index.html
        spelling error ("recordSchema") corrected
        """
        request = """<SOAP:Envelope xmlns:SOAP="http://schemas.xmlsoap.org/soap/envelope/">
  <SOAP:Body>
    <SRW:searchRetrieveRequest xmlns:SRW="http://www.loc.gov/zing/srw/">
      <SRW:version>1.1</SRW:version>
      <SRW:query>dc.author = "jones" and  dc.title = "smith"</SRW:query>
      <SRW:startRecord>1</SRW:startRecord>
      <SRW:maximumRecords>10</SRW:maximumRecords>
      <SRW:recordSchema>info:srw/schema/1/mods-v3.0</SRW:recordSchema>
    </SRW:searchRetrieveRequest>
  </SOAP:Body>
</SOAP:Envelope>"""

        observer = CallTrace(
            returnValues={
                'executeCQL': (1, ['recordId']),
            },
            methods={
                'yieldRecord': lambda identifier, partname: (g for g in ["<DATA>%s-%s</DATA>" % (identifier, partname)])
            },
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        self.sruHandler.addObserver(observer)
        response = "".join(self.srw.handleRequest(Body=request))

        echoRequest = """<srw:echoedSearchRetrieveRequest>
<srw:version>1.1</srw:version>
<srw:query>dc.author = "jones" and  dc.title = "smith"</srw:query>
<srw:startRecord>1</srw:startRecord>
<srw:maximumRecords>10</srw:maximumRecords>
<srw:recordPacking>xml</srw:recordPacking>
<srw:recordSchema>info:srw/schema/1/mods-v3.0</srw:recordSchema>
</srw:echoedSearchRetrieveRequest>"""

        self.assertEqualsWS(httpResponse % soapEnvelope % searchRetrieveResponse % (1, '<srw:records><srw:record><srw:recordSchema>info:srw/schema/1/mods-v3.0</srw:recordSchema><srw:recordPacking>xml</srw:recordPacking><srw:recordData><DATA>recordId-info:srw/schema/1/mods-v3.0</DATA></srw:recordData></srw:record></srw:records>' +echoRequest), response)


    def testConstructorVariablesAreUsed(self):
        request = soapEnvelope % SRW_REQUEST % argumentsWithMandatory % ""
        srw = Srw(
            defaultRecordSchema="DEFAULT_RECORD_SCHEMA",
            defaultRecordPacking="DEFAULT_RECORD_PACKING")
        sruParser = SruParser()
        srw.addObserver(sruParser)
        sruParser.addObserver(self.sruHandler)
        observer = CallTrace(
            returnValues={
                'executeCQL': (1, [1]),
                'yieldRecord': lambda identifier, partname: (g for g in ["<DATA>%s-%s</DATA>" % (identifier, partname)])
            },
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])

        self.sruHandler.addObserver(observer)
        response = "".join(srw.handleRequest(Body=request))
        self.assertTrue("DEFAULT_RECORD_SCHEMA" in response, response)
        self.assertTrue("DEFAULT_RECORD_PACKING" in response, response)
