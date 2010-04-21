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

from cq2utils import CQ2TestCase, CallTrace
from weightless import compose

from meresco.components.sru.diagnostic import generalSystemError

from meresco.components.drilldown import SRUTermDrilldown, DRILLDOWN_HEADER, DRILLDOWN_FOOTER, DEFAULT_MAXIMUM_TERMS


class SRUTermDrilldownTest(CQ2TestCase):
    def testSRUTermDrilldown(self):
        sruTermDrilldown = SRUTermDrilldown()

        observer = CallTrace("Drilldown")
        observer.returnValues['docsetFromQuery'] = 'docset'
        observer.returnValues['drilldown'] = iter([
                ('field0', iter([('value0_0', 14)])),
                ('field1', iter([('value1_0', 13), ('value1_1', 11)])),
                ('field2', iter([('value2_0', 3), ('value2_1', 2), ('value2_2', 1)]))])

        sruTermDrilldown.addObserver(observer)
        cqlAbstractSyntaxTree = 'cqlAbstractSyntaxTree'

        result = compose(sruTermDrilldown.extraResponseData(cqlAbstractSyntaxTree, x_term_drilldown=["field0:1,field1:2,field2"]))
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
</dd:navigator></dd:term-drilldown></dd:drilldown>""", "".join(result))
        self.assertEquals(['docsetFromQuery', 'drilldown'], [m.name for m in observer.calledMethods])
        self.assertEquals('cqlAbstractSyntaxTree', observer.calledMethods[0].args[0])
        self.assertEquals([('field0', 1, False), ('field1', 2, False), ('field2', DEFAULT_MAXIMUM_TERMS, False)], list(observer.calledMethods[1].args[1]))

    def testDrilldownCallRaisesAnError(self):
        sruTermDrilldown = SRUTermDrilldown()
        observer = CallTrace("Drilldown")
        def mockDrilldown(*args):
            raise Exception("Some Exception")
            yield "Some thing"
        observer.methods["drilldown"] = mockDrilldown
        sruTermDrilldown.addObserver(observer)

        cqlAbstractSyntaxTree = 'ignored'
        composedGenerator = compose(sruTermDrilldown.extraResponseData(cqlAbstractSyntaxTree    , x_term_drilldown=["fieldignored:1"]))
        result = "".join(composedGenerator)

        expected = DRILLDOWN_HEADER + """
            <dd:term-drilldown>
                <diagnostic xmlns="http://www.loc.gov/zing/srw/diagnostic/">
                    <uri>info://srw/diagnostics/1/1</uri>
                    <details>General System Error</details>
                    <message>Some Exception</message>
                </diagnostic>
            </dd:term-drilldown>
        """ + DRILLDOWN_FOOTER
        self.assertEqualsWS(expected, result)

    def testDrilldownInternalRaisesExceptionNotTheFirst(self):
        sruTermDrilldown = SRUTermDrilldown()
        observer = CallTrace("Drilldown")
        def raiser(*args):
            raise Exception("Some Exception")
            yield
        drilldownResults = iter([
                ('field0', iter([('value0_0', 14)])),
                ('field1', raiser()),
            ])
        observer.returnValues["drilldown"] = drilldownResults
        sruTermDrilldown.addObserver(observer)

        cqlAbstractSyntaxTree = 'ignored'

        composedGenerator = compose(sruTermDrilldown.extraResponseData(cqlAbstractSyntaxTree    , x_term_drilldown=["fieldignored:1"]))
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
        component =SRUTermDrilldown()

        result = "".join(list(component.echoedExtraRequestData(x_term_drilldown=['field0,field1'], version='1.1')))
        
        self.assertEqualsWS(DRILLDOWN_HEADER \
        + """<dd:term-drilldown>field0,field1</dd:term-drilldown>"""\
        + DRILLDOWN_FOOTER, result)
