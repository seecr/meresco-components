## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#    Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

from cq2utils import CQ2TestCase, CallTrace
from weightless.core import compose

from meresco.components.sru.diagnostic import generalSystemError

from meresco.components.drilldown import DRILLDOWN_HEADER, DRILLDOWN_FOOTER, DEFAULT_MAXIMUM_TERMS
from meresco.components.drilldown import SRUTermDrilldown

class SRUTermDrilldownTest(CQ2TestCase):
    def testSRUTermDrilldown(self):
        sruTermDrilldown = SRUTermDrilldown()

        drilldownData = iter([
                ('field0', iter([('value0_0', 14)])),
                ('field1', iter([('value1_0', 13), ('value1_1', 11)])),
                ('field2', iter([('value2_0', 3), ('value2_1', 2), ('value2_2', 1)]))])

        response = ''.join(compose(sruTermDrilldown.extraResponseData(drilldownData)))
        
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


    def testDrilldownNoResults(self):
        sruTermDrilldown = SRUTermDrilldown()
        drilldownData = iter([
                ('field0', iter([])),
            ])

        composedGenerator = compose(sruTermDrilldown.extraResponseData(drilldownData))
        result = "".join(composedGenerator)

        expected = DRILLDOWN_HEADER + """
            <dd:term-drilldown>
                <dd:navigator name="field0"/>
            </dd:term-drilldown>
        """ + DRILLDOWN_FOOTER
        self.assertEqualsWS(expected, result)

    def testDrilldownInternalRaisesExceptionNotTheFirst(self):
        sruTermDrilldown = SRUTermDrilldown()
        def raiser(*args):
            raise Exception("Some Exception")
            yield
        drilldownData = iter([
                ('field0', iter([('value0_0', 14)])),
                ('field1', raiser()),
            ])

        composedGenerator = compose(sruTermDrilldown.extraResponseData(drilldownData))
        result = "".join(composedGenerator)

        expected = DRILLDOWN_HEADER + """
            <dd:term-drilldown>
                <dd:navigator name="field0">
                    <dd:item count="14">value0_0</dd:item>
                </dd:navigator>
                <diagnostic xmlns="http://www.loc.gov/zing/srw/diagnostic/">
                    <uri>info://srw/diagnostics/1/1</uri>
                    <details>General System Error</details>
                    <message>Some Exception</message>
                </diagnostic>
            </dd:term-drilldown>
        """ + DRILLDOWN_FOOTER
        self.assertEqualsWS(expected, result)


    def testEchoedExtraRequestData(self):
        component = SRUTermDrilldown()

        result = "".join(list(component.echoedExtraRequestData(x_term_drilldown=['field0,field1'], version='1.1')))
        
        self.assertEqualsWS(DRILLDOWN_HEADER \
        + """<dd:term-drilldown>field0,field1</dd:term-drilldown>"""\
        + DRILLDOWN_FOOTER, result)
