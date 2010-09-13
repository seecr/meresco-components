## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
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

from meresco.components.sru.sruparser import MANDATORY_PARAMETER_NOT_SUPPLIED, UNSUPPORTED_PARAMETER, UNSUPPORTED_VERSION, UNSUPPORTED_OPERATION, UNSUPPORTED_PARAMETER_VALUE, QUERY_FEATURE_UNSUPPORTED, SruException, XML_HEADER
from meresco.components.sru import SruParser, SruHandler

from cq2utils import CallTrace, CQ2TestCase
from lxml.etree import parse
from StringIO import StringIO
from weightless import compose

SUCCESS = "SUCCESS"

class SruParserTest(CQ2TestCase):

    def testExplain(self):
        component = SruParser(host='TEST_SERVER_HOST', port='TEST_SERVER_PORT', description='TEST_SERVER_DESCRIPTION', modifiedDate='TEST_SERVER_DATE', database='DATABASE')

        result = "".join(list(component.handleRequest(arguments={})))
        self.assertEqualsWS("""HTTP/1.0 200 OK
Content-Type: text/xml; charset=utf-8

<?xml version="1.0" encoding="UTF-8"?>
<srw:explainResponse xmlns:srw="http://www.loc.gov/zing/srw/"
xmlns:zr="http://explain.z3950.org/dtd/2.0/">
<srw:version>1.1</srw:version>
<srw:record>
    <srw:recordPacking>xml</srw:recordPacking>
    <srw:recordSchema>http://explain.z3950.org/dtd/2.0/</srw:recordSchema>
    <srw:recordData>
        <zr:explain>
            <zr:serverInfo wsdl="http://TEST_SERVER_HOST:TEST_SERVER_PORT/DATABASE" protocol="SRU" version="1.1">
                <host>TEST_SERVER_HOST</host>
                <port>TEST_SERVER_PORT</port>
                <database>DATABASE</database>
            </zr:serverInfo>
            <zr:databaseInfo>
                <title lang="en" primary="true">SRU Database</title>
                <description lang="en" primary="true">TEST_SERVER_DESCRIPTION</description>
            </zr:databaseInfo>
            <zr:metaInfo>
                <dateModified>TEST_SERVER_DATE</dateModified>
            </zr:metaInfo>
        </zr:explain>
    </srw:recordData>
</srw:record>
</srw:explainResponse>
""", result)

    def testMandatoryArgumentsSupplied(self):
        error = MANDATORY_PARAMETER_NOT_SUPPLIED
        self.assertValid(SUCCESS, {})
        self.assertValid(error, {'version':['1.1']})
        self.assertValid(error, {'version':['1.1'], 'query':['']})
        self.assertValid(SUCCESS, {'version':['1.1'], 'query':['x'], 'operation':['searchRetrieve']})

    def testValidateAllowedArguments(self):
        error = UNSUPPORTED_PARAMETER
        self.assertValid(error, {'version':['1.1'], 'query':['x'], 'operation':['searchRetrieve'], 'niet geldig':['bla']})
        self.assertValid(SUCCESS, {'version':['1.1'], 'query':['x'], 'operation':['searchRetrieve'], 'x-whatever-comes-after-an-x': ['something']})

    def testValidVersion(self):
        error = UNSUPPORTED_VERSION
        self.assertValid(error, {'version':['1.0'], 'query':['twente'], 'operation':['searchRetrieve']})
        self.assertValid(error, {'version':['2.0'], 'query':['twente'], 'operation':['searchRetrieve']})
        self.assertValid(SUCCESS, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve']})

    def testValidOperation(self):
        error = UNSUPPORTED_OPERATION
        self.assertValid(error, {'version':['1.1'], 'query':['twente'], 'operation':['']})
        self.assertValid(error,{'version':['1.1'], 'query':['twente'], 'operation':['unsupportedOperation']})
        self.assertValid(SUCCESS, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve']})

    def testValidStartRecord(self):
        error = UNSUPPORTED_PARAMETER_VALUE
        self.assertValid(error, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'startRecord':['']})
        self.assertValid(error, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'startRecord':['A']})
        self.assertValid(error, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'startRecord':['-1']})
        self.assertValid(error, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'startRecord':['0']})
        self.assertValid(SUCCESS, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'startRecord':['1']})
        self.assertValid(SUCCESS, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'startRecord':['999999999']})

    def testValidateProperlyUTF8EncodedParameter(self):
        self.assertValid(UNSUPPORTED_PARAMETER_VALUE, {'version':['1.1'], 'query':['BadEUmlaut\xeb'], 'operation':['searchRetrieve']})

    def testValidMaximumRecords(self):
        error = UNSUPPORTED_PARAMETER_VALUE
        self.assertValid(error, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'maximumRecords':['']})
        self.assertValid(error, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'maximumRecords':['A']})
        self.assertValid(error, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'maximumRecords':['-1']})
        self.assertValid(SUCCESS, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'maximumRecords':['0']})
        self.assertValid(SUCCESS, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'maximumRecords':['1']})
        self.assertValid(SUCCESS, {'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'maximumRecords':['99']})

    def testMaximumMaximumRecords(self):
        component = SruParser('host', 'port', maximumMaximumRecords=100)
        try:
            component.parseSruArgs({'version':['1.1'], 'query':['twente'], 'operation':['searchRetrieve'], 'maximumRecords': ['101']})
            self.fail()
        except SruException, e:
            self.assertEquals(UNSUPPORTED_PARAMETER_VALUE, [e.code, e.message])

    def testValidateCQLSyntax(self):
        error = UNSUPPORTED_PARAMETER_VALUE
        self.assertValid(SUCCESS, {'version':['1.1'], 'query':['TERM'], 'operation':['searchRetrieve'], 'startRecord':['1']})
        self.assertValid(QUERY_FEATURE_UNSUPPORTED, {'version':['1.1'], 'query':['TERM1)'], 'operation':['searchRetrieve']})
        self.assertValid(QUERY_FEATURE_UNSUPPORTED, {'version':['1.1'], 'query':['"=+'], 'operation':['searchRetrieve']})

    def assertValid(self, expectedResult, arguments):
        component = SruParser('host', 'port')
        try:
            operation, arguments = component._parseArguments(arguments)
            if operation == "searchRetrieve":
                component.parseSruArgs(arguments)
            if expectedResult != SUCCESS:
                self.fail("Expected %s but got nothing"  % expectedResult)
        except SruException, e:
            self.assertEquals(expectedResult, [e.code, e.message])

    def testSearchRetrieve(self):
        component = SruParser()
        sruHandler = CallTrace('SRUHandler')
        sruHandler.returnValues['searchRetrieve'] = (x for x in ["<result>mock result XML</result>"])
        component.addObserver(sruHandler)

        response = "".join(component.handleRequest(arguments=dict(version=['1.1'], query= ['aQuery'], operation=['searchRetrieve'], startRecord=['11'], maximumRecords = ['15'])))

        self.assertEquals(['searchRetrieve'], [m.name for m in sruHandler.calledMethods])
        self.assertEquals((), sruHandler.calledMethods[0].args)
        kwargs = sruHandler.calledMethods[0].kwargs
        self.assertEquals('1.1', kwargs['version'])
        self.assertEquals('aQuery', kwargs['query'])
        self.assertEquals('searchRetrieve', kwargs['operation'])
        self.assertEquals(11, kwargs['startRecord'])
        self.assertEquals(15, kwargs['maximumRecords'])

        self.assertTrue("HTTP/1.0 200 OK" in response)
        self.assertTrue(XML_HEADER in response)


    def testSearchRetrieveWithXParameter(self):
        component = SruParser()
        sruHandler = CallTrace('SRUHandler')
        sruHandler.returnValues['searchRetrieve'] = (x for x in ["<result>mock result XML</result>"])
        component.addObserver(sruHandler)

        list(component.handleRequest(arguments={'version':['1.1'], 'query': ['aQuery'], 'operation':['searchRetrieve'], 'x-something':['something']}))

        self.assertEquals(['searchRetrieve'], [m.name for m in sruHandler.calledMethods])
        self.assertEquals((), sruHandler.calledMethods[0].args)
        kwargs = sruHandler.calledMethods[0].kwargs
        self.assertEquals(['something'], kwargs['x-something'])
        self.assertEquals(['something'], kwargs['x_something'])

