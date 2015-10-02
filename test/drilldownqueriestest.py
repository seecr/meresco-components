## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
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

from weightless.core import retval

from seecr.test import SeecrTestCase, CallTrace

from meresco.components.drilldownqueries import DrilldownQueries


class DrilldownQueriesTest(SeecrTestCase):
    def testDrilldownQuery(self):
        dbdq = DrilldownQueries()
        observer = CallTrace(methods=dict(executeQuery=mockExecuteQuery))
        dbdq.addObserver(observer)

        result = retval(dbdq.executeQuery(extraArguments={'x-drilldown-query': ['a = b']}))
        self.assertEquals('result', result)
        self.assertEquals(['executeQuery'], observer.calledMethodNames())
        executeQueryMethod = observer.calledMethods[0]
        self.assertEquals([('a', ['b'])], executeQueryMethod.kwargs['drilldownQueries'])

        observer.calledMethods.reset()

        result = retval(dbdq.executeQuery(extraArguments={'x-drilldown-query': ['a exact b']}))
        self.assertEquals('result', result)
        self.assertEquals(['executeQuery'], observer.calledMethodNames())
        executeQueryMethod = observer.calledMethods[0]
        self.assertEquals([('a', ['b'])], executeQueryMethod.kwargs['drilldownQueries'])

    def testErrorForInvalidFormatDrilldownQuery(self):
        dbdq = DrilldownQueries()
        observer = CallTrace(methods=dict(executeQuery=mockExecuteQuery))
        dbdq.addObserver(observer)

        try:
            retval(dbdq.executeQuery(extraArguments={'x-drilldown-query': ['a']}))
            self.fail()
        except ValueError, e:
            self.assertEquals('x-drilldown-query format should be field=value', str(e))
        self.assertEquals([], observer.calledMethodNames())

    def testNoDrilldownQuery(self):
        dbdq = DrilldownQueries()
        observer = CallTrace(methods=dict(executeQuery=mockExecuteQuery))
        dbdq.addObserver(observer)
        result = retval(dbdq.executeQuery(extraArguments={}, query='*'))
        self.assertEquals('result', result)
        self.assertEquals(['executeQuery'], observer.calledMethodNames())
        executeQueryMethod = observer.calledMethods[0]
        self.assertEquals([], executeQueryMethod.kwargs['drilldownQueries'])
        self.assertEquals("*", executeQueryMethod.kwargs['query'])


def mockExecuteQuery(**kwargs):
    raise StopIteration('result')
    yield
