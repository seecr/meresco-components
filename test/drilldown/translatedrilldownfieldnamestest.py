## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2012 Stichting Kennisnet http://www.kennisnet.nl
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
from weightless.core import be, compose
from meresco.core import Observable
from meresco.components.facetindex import Response

from meresco.components.drilldown import TranslateDrilldownFieldnames

class TranslateDrilldownFieldnamesTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.response = Response(total=10, hits=[])
        def executeQuery(fieldnamesAndMaximums=None, **kwargs):
            if not fieldnamesAndMaximums is None:
                self.response.drilldownData = []
                for fieldName, _, _ in fieldnamesAndMaximums:
                    self.response.drilldownData.append((fieldName,  [('value1', 1), ('value2', 2)]))
            raise StopIteration(self.response)
            yield
        self.observer = CallTrace('observer', methods={'executeQuery': executeQuery})

    def testTranslate(self):
        names = {
            'name1': 'internal.name1',
            'name2': 'internal.name2',
            'othername1': 'internal.name1',
        }
        result = self._doDrilldown(
                translate=names.get,
                queryKwargs=dict(
                    query='query', 
                    fieldnamesAndMaximums=[('name1', 10, True)]))

        self.assertEquals(['executeQuery'], [m.name for m in self.observer.calledMethods])
        self.assertEquals(dict(query='query', fieldnamesAndMaximums=[('internal.name1', 10, True)]), self.observer.calledMethods[0].kwargs)
        self.assertEquals(self.response.hits, result.hits)
        self.assertEquals(self.response.total, result.total)
        self.assertEquals([
            ('name1', [('value1', 1), ('value2', 2)]),
        ], result.drilldownData)

    def testNoDrilldown(self):
        result = self._doDrilldown(
                translate=lambda name: 'ignored',
                queryKwargs=dict(query='query'))

        self.assertEquals("[executeQuery(query='query')]", str(self.observer.calledMethods))
        self.assertEquals(self.response.hits, result.hits)
        self.assertEquals(self.response.total, result.total)
        self.assertFalse(hasattr(result, 'drilldownData'))

    def testFieldnamesAndMaximumsNone(self):
        result = self._doDrilldown(
                translate=lambda name: 'ignored',
                queryKwargs=dict(
                    query='query', 
                    fieldnamesAndMaximums=None))

        self.assertEquals("[executeQuery(query='query')]", str(self.observer.calledMethods))
        self.assertEquals(self.response.hits, result.hits)
        self.assertEquals(self.response.total, result.total)
        self.assertFalse(hasattr(result, 'drilldownData'))


    def _doDrilldown(self, translate, queryKwargs):
        observable = be(
            (Observable(),
                (TranslateDrilldownFieldnames(translate=translate),
                    (self.observer,)
                )
            )
        )
        try:
            compose(observable.any.executeQuery(**queryKwargs)).next()
        except StopIteration, e:
            return e.args[0]

