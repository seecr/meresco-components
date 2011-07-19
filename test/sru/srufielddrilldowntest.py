# -*- coding: utf-8 -*-
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
from utils import asyncreturn

from StringIO import StringIO

from meresco.core import be, decorateWith
from meresco.components.facetindex import Response
from meresco.components.drilldown import SRUFieldDrilldown, DRILLDOWN_HEADER, DRILLDOWN_FOOTER

from weightless.core import compose

from cqlparser import parseString, cql2string

class SRUFieldDrilldownTest(CQ2TestCase):

    def testSRUParamsAndXMLOutput(self):
        firstCall = []
        def executeQuery(**kwargs):
            if not firstCall:
                firstCall.append(True)
                raise StopIteration(Response(total=5, hits=range(5)))
            else:
                raise StopIteration(Response(total=10, hits=range(10)))
        sruFieldDrilldown = SRUFieldDrilldown()
        observer = CallTrace("observer")
        sruFieldDrilldown.addObserver(observer)
        observer.methods["executeQuery"] = executeQuery

        result = compose(sruFieldDrilldown.extraResponseData(x_field_drilldown=['term'], x_field_drilldown_fields=['field0,field1'], query='original'))
        self.assertEqualsWS(DRILLDOWN_HEADER + """<dd:field-drilldown>
<dd:field name="field0">5</dd:field>
<dd:field name="field1">10</dd:field></dd:field-drilldown></dd:drilldown>""", "".join(result))

        self.assertEquals(['executeQuery', 'executeQuery'], [m.name for m in observer.calledMethods])
        self.assertEquals(['cqlAbstractSyntaxTree', 'cqlAbstractSyntaxTree'], [','.join((m.kwargs.keys())) for m in observer.calledMethods])
        self.assertEquals('(original) AND field0=term', cql2string(observer.calledMethods[0].kwargs['cqlAbstractSyntaxTree']))
        self.assertEquals('(original) AND field1=term', cql2string(observer.calledMethods[1].kwargs['cqlAbstractSyntaxTree']))

    def testDrilldown(self):
        adapter = SRUFieldDrilldown()
        observer = CallTrace("Observer")
        observer.exceptions["executeQuery"] = StopIteration(Response(total=16, hits=range(16)))
        adapter.addObserver(observer)
        result = asyncreturn(adapter.drilldown, 'original', 'term', ['field0', 'field1'])
        self.assertEquals(2, len(observer.calledMethods))
        self.assertEquals("executeQuery(cqlAbstractSyntaxTree=<class CQL_QUERY>)", str(observer.calledMethods[0]))
        self.assertEquals(parseString("(original) and field0=term"),  observer.calledMethods[0].kwargs['cqlAbstractSyntaxTree'])
        self.assertEquals([("field0", 16), ("field1", 16)], result)

    def testEchoedExtraRequestData(self):
        d = SRUFieldDrilldown()
        result = "".join(d.echoedExtraRequestData(x_field_drilldown=['term'], x_field_drilldown_fields = ['field0,field1'], otherArgument=['ignored']))
        self.assertEquals(DRILLDOWN_HEADER + '<dd:field-drilldown>term</dd:field-drilldown><dd:field-drilldown-fields>field0,field1</dd:field-drilldown-fields></dd:drilldown>', result)

