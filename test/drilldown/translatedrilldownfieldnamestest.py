## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2012-2014, 2017, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012, 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2012-2013, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2017 SURFmarket http://www.surf.nl
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
from weightless.core import be, compose, consume
from meresco.core import Observable
from testhelpers import Response
from meresco.components.sru.sruhandler import DRILLDOWN_SORTBY_INDEX

from meresco.components.drilldown import TranslateDrilldownFieldnames

class TranslateDrilldownFieldnamesTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.response = Response(total=10, hits=[])
        self.drilldownDataResponse = None
        def executeQuery(facets=None, **kwargs):
            if self.drilldownDataResponse:
                self.response.drilldownData = self.drilldownDataResponse
            elif not facets is None:
                self.response.drilldownData = []
                for facet in facets:
                    if isinstance(facet, dict):
                        self.response.drilldownData.append({'fieldname': facet['fieldname'], 'terms':[{'term': 'value1', 'count': 1}, {'term': 'value2', 'count': 2}]})
            raise StopIteration(self.response)
            yield
        self.observer = CallTrace('observer', methods={'executeQuery': executeQuery}, emptyGeneratorMethods=['someMethod'])

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
                    facets=[dict(fieldname='name1', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX)]))

        self.assertEqual(['executeQuery'], [m.name for m in self.observer.calledMethods])
        self.assertEqual(dict(query='query', facets=[dict(fieldname='internal.name1', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX)]), self.observer.calledMethods[0].kwargs)
        self.assertEqual(self.response.hits, result.hits)
        self.assertEqual(self.response.total, result.total)
        self.assertEqual([
            {
                'fieldname': 'name1',
                'terms': [
                    {'term': 'value1', 'count': 1}, {'term': 'value2', 'count': 2}
                ]
            }
        ], result.drilldownData)

    def testTranslatePivotFacets(self):
        names = {
            'name1': 'internal.name1',
            'name2': 'internal.name2',
            'name3': 'internal.name3',
        }

        self.drilldownDataResponse = [
            {
                'fieldname': 'internal.name1',
                'terms':[
                    {   'term': 'value1',
                        'count': 1,
                        'pivot': {
                            'fieldname': 'internal.name2',
                            'terms':[
                                {   'term': 'value2',
                                    'count': 1
                                },
                            ]
                        }
                    }
                ],
            },
            {
                'fieldname': 'internal.name3',
                'terms':[
                    {   'term': 'value3',
                        'count': 1
                    }
                ]
            }
        ]
        result = self._doDrilldown(
                translate=names.get,
                queryKwargs=dict(
                    query='query',
                    facets=[
                        [
                            dict(fieldname='name1', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX),
                            dict(fieldname='name2', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX)
                        ],
                        dict(fieldname='name3', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX)
                    ]
                )
            )

        self.assertEqual(['executeQuery'], [m.name for m in self.observer.calledMethods])
        self.assertEqual([
                        [
                            dict(fieldname='internal.name1', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX),
                            dict(fieldname='internal.name2', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX)
                        ],
                        dict(fieldname='internal.name3', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX)
                    ], self.observer.calledMethods[0].kwargs['facets'])
        self.assertEqual(self.response.hits, result.hits)
        self.assertEqual(self.response.total, result.total)
        self.assertEqual([
            {
                'fieldname': 'name1',
                'terms':[
                    {   'term': 'value1',
                        'count': 1,
                        'pivot': {
                            'fieldname': 'name2',
                            'terms':[
                                {   'term': 'value2',
                                    'count': 1
                                },
                            ]
                        }
                    }
                ],
            },
            {
                'fieldname': 'name3',
                'terms':[
                    {   'term': 'value3',
                        'count': 1
                    }
                ]
            }
        ], result.drilldownData)

    def testTranslateSubtermsFacets(self):
        names = {
            'name1': 'internal.name1',
            'name2': 'internal.name2',
            'name3': 'internal.name3',
        }

        self.drilldownDataResponse = [
            {
                'fieldname': 'internal.name1',
                'terms':[
                    {   'term': 'value1',
                        'count': 1,
                        'subterms': [
                            {   'term': 'value2',
                                'count': 1
                            },
                        ]
                    }
                ],
            },
            {
                'fieldname': 'internal.name3',
                'terms':[
                    {   'term': 'value3',
                        'count': 1
                    }
                ]
            }
        ]
        result = self._doDrilldown(
                translate=names.get,
                queryKwargs=dict(
                    query='query',
                    facets=[
                        [
                            dict(fieldname='name1', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX),
                            dict(fieldname='name2', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX)
                        ],
                        dict(fieldname='name3', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX)
                    ]
                )
            )

        self.assertEqual(['executeQuery'], [m.name for m in self.observer.calledMethods])
        self.assertEqual([
                        [
                            dict(fieldname='internal.name1', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX),
                            dict(fieldname='internal.name2', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX)
                        ],
                        dict(fieldname='internal.name3', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX)
                    ], self.observer.calledMethods[0].kwargs['facets'])
        self.assertEqual(self.response.hits, result.hits)
        self.assertEqual(self.response.total, result.total)
        self.assertEqual([
            {
                'fieldname': 'name1',
                'terms':[
                    {   'term': 'value1',
                        'count': 1,
                        'subterms': [
                            {   'term': 'value2',
                                'count': 1
                            },
                        ]
                    }
                ],
            },
            {
                'fieldname': 'name3',
                'terms':[
                    {   'term': 'value3',
                        'count': 1
                    }
                ]
            }
        ], result.drilldownData)


    def testNoDrilldown(self):
        result = self._doDrilldown(
                translate=lambda name: 'ignored',
                queryKwargs=dict(query='query'))

        self.assertEqual("[executeQuery(query='query')]", str(self.observer.calledMethods))
        self.assertEqual(self.response.hits, result.hits)
        self.assertEqual(self.response.total, result.total)
        self.assertFalse(hasattr(result, 'drilldownData'))

    def testFacetsNone(self):
        result = self._doDrilldown(
                translate=lambda name: 'ignored',
                queryKwargs=dict(
                    query='query',
                    facets=None))

        self.assertEqual("[executeQuery(query='query')]", str(self.observer.calledMethods))
        self.assertEqual(self.response.hits, result.hits)
        self.assertEqual(self.response.total, result.total)
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
            next(compose(observable.any.executeQuery(**queryKwargs)))
        except StopIteration as e:
            return e.args[0]

    def testPassThrough(self):
        observable = be(
            (Observable(),
                (TranslateDrilldownFieldnames(translate=lambda:'ignore'),
                    (self.observer,)
                )
            )
        )
        consume(observable.any.someMethod(field='whatever'))
        self.assertEqual(['someMethod'], self.observer.calledMethodNames())

    def testSameTranslationForMultipleNames(self):
        translate = lambda name: 'internal.name'
        result = self._doDrilldown(
                translate=translate,
                queryKwargs=dict(
                    query='query',
                    facets=[dict(fieldname='name1', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX),
                            dict(fieldname='name2', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX),
                            dict(fieldname='name3', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX)]))

        self.assertEquals(['executeQuery'], [m.name for m in self.observer.calledMethods])
        self.assertEquals(dict(query='query', facets=[
            dict(fieldname='internal.name', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX),
            dict(fieldname='internal.name', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX),
            dict(fieldname='internal.name', maxTerms=10, sortBy=DRILLDOWN_SORTBY_INDEX),
            ]), self.observer.calledMethods[0].kwargs)
        self.assertEquals(self.response.hits, result.hits)
        self.assertEquals(self.response.total, result.total)
        self.assertEquals([ {
                'fieldname': 'name1',
                'terms': [ {'term': 'value1', 'count': 1}, {'term': 'value2', 'count': 2} ]
            }, {
                'fieldname': 'name2',
                'terms': [ {'term': 'value1', 'count': 1}, {'term': 'value2', 'count': 2} ]
            }, {
                'fieldname': 'name3',
                'terms': [ {'term': 'value1', 'count': 1}, {'term': 'value2', 'count': 2} ]
            }], result.drilldownData)



