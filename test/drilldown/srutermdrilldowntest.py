## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011-2013 Stichting Kennisnet http://www.kennisnet.nl
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
from lxml.etree import parse, XML
from StringIO import StringIO
from simplejson import loads
from os.path import join, dirname, basename

from seecr.test.io import stderr_replace_decorator

from meresco.components.drilldown import DRILLDOWN_HEADER, DRILLDOWN_FOOTER
from meresco.components.drilldown.drilldown import _DRILLDOWN_HEADER, _DRILLDOWN_XSD_2013
from meresco.components.drilldown import SRUTermDrilldown
from meresco.components.drilldown.srutermdrilldown import FORMAT_JSON, FORMAT_XML
from meresco.components.xml_generic.validate import assertValid
from meresco.components.xml_generic import schemasPath
from meresco.xml import xpathFirst, namespaces

class SRUTermDrilldownTest(SeecrTestCase):
    def testSRUTermDrilldown(self):
        sruTermDrilldown = SRUTermDrilldown()

        drilldownData = [
                {'fieldname': 'field0', 'terms': [{'term': 'value0_0', 'count': 14}]},
                {'fieldname': 'field1', 'terms': [{'term': 'value1_0', 'count': 13}, {'term': 'value1_1', 'count': 11}]},
                {'fieldname': 'field2', 'terms': [{'term': 'value2_0', 'count': 3}, {'term': 'value2_1', 'count': 2}, {'term': 'value2_2', 'count': 1}]}
        ]

        response = ''.join(compose(sruTermDrilldown.extraResponseData(drilldownData, sruArguments={})))

        self.assertEqualsWS(DRILLDOWN_HEADER + """<dd:term-drilldown><dd:navigator name="field0">
    <dd:item count="14">value0_0</dd:item>
</dd:navigator>
<dd:navigator name="field1">
    <dd:item count="13">value1_0</dd:item>
    <dd:item count="11">value1_1</dd:item>
</dd:navigator>
<dd:navigator name="field2">
    <dd:item count="3">value2_0</dd:item>
    <dd:item count="2">value2_1</dd:item>
    <dd:item count="1">value2_2</dd:item>
</dd:navigator></dd:term-drilldown></dd:drilldown>""", response)

        xsdFilename = self._getXsdFilename(response)
        assertValid(response, join(schemasPath, xsdFilename))

    def testSRUTermDrilldownWithPivots(self):
        sruTermDrilldown = SRUTermDrilldown(defaultFormat=FORMAT_XML)

        drilldownData = [
                {
                    'fieldname': 'field0',
                    'terms': [
                        {
                            'term': 'value0',
                            'count': 1,
                            'pivot': {
                                'fieldname': 'field1',
                                'terms': [
                                    {
                                        'term': 'value0_0',
                                        'count': 10,
                                    },
                                    {
                                        'term': 'value0_1',
                                        'count': 20
                                    }
                                ]
                            }
                        },
                        {
                            'term': 'value1',
                            'count': 2
                        }
                    ]
                }
            ]

        response = ''.join(compose(sruTermDrilldown.extraResponseData(drilldownData, sruArguments={})))

        self.assertEqualsWS(_DRILLDOWN_HEADER % _DRILLDOWN_XSD_2013 + """<dd:term-drilldown><dd:navigator name="field0">
    <dd:item count="1" value="value0">
        <dd:navigator name="field1">
            <dd:item count="10" value="value0_0"/>
            <dd:item count="20" value="value0_1"/>
        </dd:navigator>
    </dd:item>
    <dd:item count="2" value="value1"/>
</dd:navigator></dd:term-drilldown></dd:drilldown>""", response)
        xsdFilename = self._getXsdFilename(response)
        assertValid(response, join(schemasPath, xsdFilename))

    def testSRUTermDrilldownWithPivotsInJson(self):
        sruTermDrilldown = SRUTermDrilldown(defaultFormat=FORMAT_JSON)

        drilldownData = [
                {
                    'fieldname': 'field0',
                    'terms': [
                        {
                            'term': 'value0',
                            'count': 1,
                            'pivot': {
                                'fieldname': 'field1',
                                'terms': [
                                    {
                                        'term': 'value0_0',
                                        'count': 10,
                                    },
                                    {
                                        'term': 'value0 & 1',
                                        'count': 20
                                    }
                                ]
                            }
                        },
                        {
                            'term': 'value1',
                            'count': 2
                        }
                    ]
                }
            ]

        response = ''.join(compose(sruTermDrilldown.extraResponseData(drilldownData, sruArguments={'x-drilldown-format': ['json']})))
        self.assertEquals(drilldownData, loads(xpathFirst(XML(response), '//drilldown:term-drilldown/drilldown:json/text()')))

        xsdFilename = self._getXsdFilename(response)
        assertValid(response, join(schemasPath, xsdFilename))

    def testDrilldownNoResults(self):
        sruTermDrilldown = SRUTermDrilldown()
        drilldownData = [
                {'fieldname': 'field0', 'terms': []},
            ]

        composedGenerator = compose(sruTermDrilldown.extraResponseData(drilldownData, sruArguments={}))
        result = "".join(composedGenerator)

        expected = DRILLDOWN_HEADER + """
            <dd:term-drilldown>
                <dd:navigator name="field0"/>
            </dd:term-drilldown>
        """ + DRILLDOWN_FOOTER
        self.assertEqualsWS(expected, result)

    def testDefaultFormat(self):
        self.assertRaises(ValueError, lambda: SRUTermDrilldown(defaultFormat='text'))
        sruTermDrilldown = SRUTermDrilldown(defaultFormat='json')
        drilldownData = [
                {
                    'fieldname': 'field0',
                    'terms': [
                        {
                            'term': 'value0',
                            'count': 1,
                        }
                    ]
                }
            ]

        response = parse(StringIO(''.join(compose(sruTermDrilldown.extraResponseData(drilldownData, sruArguments={})))))

        self.assertEquals(drilldownData, loads(xpathFirst(response, '//drilldown:term-drilldown/drilldown:json/text()')))

    @stderr_replace_decorator
    def testWrongFormat(self):
        sruTermDrilldown = SRUTermDrilldown()
        drilldownData = [
                {
                    'fieldname': 'field0',
                    'terms': [
                        {
                            'term': 'value0',
                            'count': 1,
                        }
                    ]
                }
            ]

        response = parse(StringIO(''.join(compose(sruTermDrilldown.extraResponseData(drilldownData, sruArguments={'x-drilldown-format':'text'})))))

        self.assertEqualsWS("Expected x-drilldown-format to be one of: ['xml', 'json']", xpathFirst(response, '//drilldown:term-drilldown/diag:diagnostic/diag:message/text()'))


    def testEchoedExtraRequestData(self):
        component = SRUTermDrilldown()

        result = "".join(list(component.echoedExtraRequestData(sruArguments={'x-term-drilldown': ['field0,field1'], 'version': '1.1'}, version='1.1')))

        self.assertEqualsWS(DRILLDOWN_HEADER \
        + """<dd:term-drilldown>field0,field1</dd:term-drilldown>"""\
        + DRILLDOWN_FOOTER, result)

    def testEchoedExtraRequestDataWithJsonFormat(self):
        component = SRUTermDrilldown()

        result = "".join(list(component.echoedExtraRequestData(sruArguments={'x-term-drilldown': ['field0/field1,field2','field3'], 'version': '1.1', 'x-drilldown-format': ['json']}, version='1.1')))

        self.assertEqualsWS(_DRILLDOWN_HEADER % _DRILLDOWN_XSD_2013 + """
            <dd:request>
                <dd:x-term-drilldown>field0/field1</dd:x-term-drilldown>
                <dd:x-term-drilldown>field2</dd:x-term-drilldown>
                <dd:x-term-drilldown>field3</dd:x-term-drilldown>
                <dd:x-drilldown-format>json</dd:x-drilldown-format>
            </dd:request>""" +\
            DRILLDOWN_FOOTER, result)

        xsdFilename = self._getXsdFilename(result)
        assertValid(result, join(schemasPath, xsdFilename))
        assertValid(open(join(schemasPath, xsdFilename)).read(), join(schemasPath, 'XMLSchema.xsd'))

    def testEchoedExtraRequestDataWithEmptyTermDrilldownFormat(self):
        component = SRUTermDrilldown(defaultFormat=FORMAT_XML)

        result = "".join(list(component.echoedExtraRequestData(sruArguments={'x-term-drilldown': [''], 'version': '1.1'}, version='1.1')))

        self.assertEqualsWS("", result)

    def _getXsdFilename(self, response):
        schemaLocation = xpathFirst(XML(response), '/drilldown:drilldown/@xsi:schemaLocation')
        namespace, xsd = schemaLocation.split()
        self.assertEquals(namespaces['drilldown'], namespace)
        self.assertEquals('http://meresco.org/files/xsd', dirname(xsd))
        return basename(xsd)

