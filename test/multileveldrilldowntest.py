## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2008-2009 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2008-2009 Technische Universiteit Delft http://www.tudelft.nl
# Copyright (C) 2008-2009 Universiteit van Tilburg http://www.uvt.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import CallTrace
from unittest import TestCase
from meresco.core import Observable
from weightless.core import compose

from meresco.components import MultiLevelDrilldown, MultiLevelDrilldownException

class MultiLevelDrilldownTest(TestCase):
    def testOne(self):
        observable = Observable()
        bitMatrixRow = CallTrace('BitMatrixRow')
        multi = MultiLevelDrilldown(
            {'date':[('datelevel1', 10, False)]}
        )
        drilldown = CallTrace('Drilldown')
        def dd(*args, **kwargs):
            raise StopIteration(iter([('datelevel1', iter([('2008',13),('2007',10)]))]))
            yield
        drilldown.methods['drilldown'] = dd
        multi.addObserver(drilldown)
        observable.addObserver(multi)

        result = list(compose(observable.call.multiLevelDrilldown(bitMatrixRow, ['date'])))

        self.assertEqual(1, len(drilldown.calledMethods))
        drilldownMethod = drilldown.calledMethods[0]
        self.assertEqual('drilldown', drilldownMethod.name)
        self.assertEqual((bitMatrixRow, [('datelevel1', 10, False)]), drilldownMethod.args)
        self.assertEqual(1, len(result))
        (inputFieldName, realFieldName), termCounts = result[0]
        self.assertEqual('date', inputFieldName)
        self.assertEqual('datelevel1', realFieldName)
        self.assertEqual([('2008',13),('2007',10)], list(termCounts))

    def testTwoFieldNamesCalled(self):
        multi = MultiLevelDrilldown(
            {'date':[('datelevel2',3, False),('datelevel1', 10, False)],
             'genre':[('type', 10, False)]
            }
        )
        drilldown = CallTrace('Drilldown')
        doDrilldownArguments = []
        def doDrilldown(bitMatrixRow, fieldNamesAndMaxResults):
            doDrilldownArguments.append((bitMatrixRow, fieldNamesAndMaxResults))
            self.assertEqual(1, len(fieldNamesAndMaxResults))
            levelField, levelMax, levelSorted = fieldNamesAndMaxResults[0]
            if 'datelevel2' == levelField:
                raise StopIteration(iter([('datelevel2', iter([('2008',13),('2007',10)][:levelMax]))]))
            else:
                raise StopIteration(iter([('type', iter([('literature',43),('donaldduck',30)][:levelMax]))]))
            yield
        drilldown.drilldown = doDrilldown
        multi.addObserver(drilldown)

        result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['date', 'genre'])))

        self.assertEqual(2, len(doDrilldownArguments))
        self.assertEqual(('bitMatrixRow', [('datelevel2', 3, False)]), doDrilldownArguments[0])
        self.assertEqual(('bitMatrixRow', [('type', 10, False)]), doDrilldownArguments[1])
        self.assertEqual(2, len(result))
        self.assertEqual([('date', 'datelevel2'),('genre', 'type')], [(inField, realField) for (inField, realField), termCounts in result])

    def testFieldWithMultiLevel(self):
        multi = MultiLevelDrilldown(
            {'date':[('yearAndMonth', 2, False), ('year', 2, False)]
            }
        )
        drilldown = CallTrace('Drilldown')
        doDrilldownArguments = []
        def doDrilldown(bitMatrixRow, fieldNamesAndMaxResults):
            doDrilldownArguments.append((bitMatrixRow, fieldNamesAndMaxResults))
            self.assertEqual(1, len(fieldNamesAndMaxResults))
            levelField, levelMax, levelSorted = fieldNamesAndMaxResults[0]
            if levelField == 'yearAndMonth':
                raise StopIteration(iter([('yearAndMonth', iter([('2008-01',11),('2008-02',2),('2007-12',1)][:levelMax]))]))
            else:
                raise StopIteration(iter([('year', iter([('2008',13),('2003',10),('2007',10)][:levelMax]))]))
            yield
        drilldown.drilldown = doDrilldown
        multi.addObserver(drilldown)

        result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['date'])))

        self.assertEqual(2, len(doDrilldownArguments))
        self.assertEqual(('bitMatrixRow', [('yearAndMonth', 2, False)]), doDrilldownArguments[0])
        self.assertEqual(('bitMatrixRow', [('year', 2, False)]), doDrilldownArguments[1])
        self.assertEqual(1, len(result))
        (inField, realField), termCounts = result[0]
        self.assertEqual('year', realField)
        self.assertEqual([('2008',13),('2003',10)], list(termCounts))

    def testFieldDoesNotExist(self):
        bitMatrixRow = CallTrace('BitMatrixRow')
        multi = MultiLevelDrilldown(
            {'date':[('datelevel1', 10, False)]}
        )
        drilldown = CallTrace('Drilldown')
        drilldown.returnValues['drilldown'] = iter([('datelevel1', iter([('2008',13),('2007',10)]))])
        multi.addObserver(drilldown)

        try:
            result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['doesNotExist'])))
            self.fail()
        except MultiLevelDrilldownException as e:
            self.assertTrue('doesNotExist' in str(e), e)

    def testLastOneDoesnotReturnValue(self):
        multi = MultiLevelDrilldown(
            {'date':[('yearAndMonth', 2, False), ('year', 2, False)]
            }
        )
        drilldown = CallTrace('Drilldown')
        doDrilldownArguments = []
        def doDrilldown(bitMatrixRow, fieldNamesAndMaxResults):
            doDrilldownArguments.append((bitMatrixRow, fieldNamesAndMaxResults))
            self.assertEqual(1, len(fieldNamesAndMaxResults))
            levelField, levelMax, levelSorted = fieldNamesAndMaxResults[0]
            if levelField == 'yearAndMonth':
                raise StopIteration(iter([('yearAndMonth', iter([('2008-01',11),('2008-02',2),('2007-12',1)][:levelMax]))]))
            else:
                raise StopIteration(iter([('year', iter([]))]))
            yield
        drilldown.drilldown = doDrilldown
        multi.addObserver(drilldown)

        result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['date'])))

        self.assertEqual(2, len(doDrilldownArguments))
        self.assertEqual(('bitMatrixRow', [('yearAndMonth', 2, False)]), doDrilldownArguments[0])
        self.assertEqual(('bitMatrixRow', [('year', 2, False)]), doDrilldownArguments[1])
        self.assertEqual(1, len(result))
        (inField, realField), termCounts = result[0]
        self.assertEqual('yearAndMonth', realField)
        self.assertEqual([('2008-01',11),('2008-02',2)], list(termCounts))

    def testLastZeroReturnValue(self):
        multi = MultiLevelDrilldown(
            {'date':[('yearAndMonth', 2, False), ('year', 2, False)]
            }
        )
        drilldown = CallTrace('Drilldown')
        doDrilldownArguments = []
        def doDrilldown(bitMatrixRow, fieldNamesAndMaxResults):
            doDrilldownArguments.append((bitMatrixRow, fieldNamesAndMaxResults))
            self.assertEqual(1, len(fieldNamesAndMaxResults))
            levelField, levelMax, sorted = fieldNamesAndMaxResults[0]
            if levelField == 'yearAndMonth':
                raise StopIteration(iter([('yearAndMonth', iter([]))]))
            else:
                raise StopIteration(iter([('year', iter([]))]))
            yield
        drilldown.drilldown = doDrilldown
        multi.addObserver(drilldown)

        result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['date'])))

        self.assertEqual(1, len(result))
        (inField, realField), termCounts = result[0]
        self.assertEqual(None, realField)

    def testWithSorting(self):
        mockData = {
            'yearAndMonth': [('2008-01',1),('2008-02',2),('2007-12',11)],
            'year': [('2008',13),('2003',10),('2005',9), ('2007', 15)]
        }
        drilldown = CallTrace('Drilldown')
        def doDrilldown(bitMatrixRow, fieldNamesAndMaxResults):
            levelField, levelMax, levelSorted = fieldNamesAndMaxResults[0]
            data = mockData[levelField]
            if levelSorted:
                def _cmp(l, r):
                    term0, card0 = l
                    term1, card1 = r
                    return cmp(card1, card0)
                data = sorted(data, cmp=_cmp)
            if levelMax > 0:
                data = data[:levelMax]
            raise StopIteration(iter([(levelField, iter(data))]))
            yield
        drilldown.drilldown = doDrilldown

        multi = MultiLevelDrilldown({'date':[('yearAndMonth', 2, False), ('year', 3, True)]})
        multi.addObserver(drilldown)
        result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['date'])))
        self.assertEqual([(('date', 'year'), [('2007', 15), ('2008', 13), ('2003', 10)])], result)

        multi = MultiLevelDrilldown({'date':[('yearAndMonth', 4, False), ('year', 3, False)]})
        multi.addObserver(drilldown)

        result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['date'])))
        self.assertEqual([(('date', 'yearAndMonth'), [('2008-01',1),('2008-02',2),('2007-12',11)])], result)



