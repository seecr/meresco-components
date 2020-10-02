## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015-2016 Drents Archief http://www.drentsarchief.nl
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
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.dbdq = DrilldownQueries()
        self.observer = CallTrace(methods=dict(executeQuery=mockExecuteQuery))
        self.dbdq.addObserver(self.observer)


    def testDrilldownQuery(self):
        result = retval(self.dbdq.executeQuery(extraArguments={'x-drilldown-query': ['a = b']}))
        self.assertEqual('result', result)
        self.assertEqual(['executeQuery'], self.observer.calledMethodNames())
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual([('a', ['b'])], executeQueryMethod.kwargs['drilldownQueries'])

        self.observer.calledMethods.reset()

        result = retval(self.dbdq.executeQuery(extraArguments={'x-drilldown-query': ['a exact b']}))
        self.assertEqual('result', result)
        self.assertEqual(['executeQuery'], self.observer.calledMethodNames())
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual([('a', ['b'])], executeQueryMethod.kwargs['drilldownQueries'])

    def testErrorForInvalidFormatDrilldownQuery(self):
        try:
            retval(self.dbdq.executeQuery(extraArguments={'x-drilldown-query': ['a']}))
            self.fail()
        except ValueError as e:
            self.assertEqual('x-drilldown-query format should be field=value', str(e))
        self.assertEqual([], self.observer.calledMethodNames())

    def testNoDrilldownQuery(self):
        result = retval(self.dbdq.executeQuery(extraArguments={}, query='*'))
        self.assertEqual('result', result)
        self.assertEqual(['executeQuery'], self.observer.calledMethodNames())
        executeQueryMethod = self.observer.calledMethods[0]
        self.assertEqual([], executeQueryMethod.kwargs['drilldownQueries'])
        self.assertEqual("*", executeQueryMethod.kwargs['query'])


def mockExecuteQuery(**kwargs):
    raise StopIteration('result')
    yield
