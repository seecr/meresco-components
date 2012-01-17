## begin license ##
#
#    "Delft-Tilburg" (delfttilburg) is a package containing shared code
#    between the Delft "Discover" and Tilburg "Beter Zoeken & Vinden" projects.
#    Both projects are based on Meresco Software (http://meresco.com)
#    Copyright (C) 2008-2009 Technische Universiteit Delft http://www.tudelft.nl
#    Copyright (C) 2008-2009 Universiteit van Tilburg http://www.uvt.nl
#    Copyright (C) 2008-2009 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of "Delft-Tilburg".
#
#    "Delft-Tilburg" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "Delft-Tilburg" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "Delft-Tilburg"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
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

        self.assertEquals(1, len(drilldown.calledMethods))
        drilldownMethod = drilldown.calledMethods[0]
        self.assertEquals('drilldown', drilldownMethod.name)
        self.assertEquals((bitMatrixRow, [('datelevel1', 10, False)]), drilldownMethod.args)
        self.assertEquals(1, len(result))
        (inputFieldName, realFieldName), termCounts = result[0]
        self.assertEquals('date', inputFieldName)
        self.assertEquals('datelevel1', realFieldName)
        self.assertEquals([('2008',13),('2007',10)], list(termCounts))

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
            self.assertEquals(1, len(fieldNamesAndMaxResults))
            levelField, levelMax, levelSorted = fieldNamesAndMaxResults[0]
            if 'datelevel2' == levelField:
                raise StopIteration(iter([('datelevel2', iter([('2008',13),('2007',10)][:levelMax]))]))
            else:
                raise StopIteration(iter([('type', iter([('literature',43),('donaldduck',30)][:levelMax]))]))
            yield
        drilldown.drilldown = doDrilldown
        multi.addObserver(drilldown)

        result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['date', 'genre'])))

        self.assertEquals(2, len(doDrilldownArguments))
        self.assertEquals(('bitMatrixRow', [('datelevel2', 3, False)]), doDrilldownArguments[0])
        self.assertEquals(('bitMatrixRow', [('type', 10, False)]), doDrilldownArguments[1])
        self.assertEquals(2, len(result))
        self.assertEquals([('date', 'datelevel2'),('genre', 'type')], [(inField, realField) for (inField, realField), termCounts in result])

    def testFieldWithMultiLevel(self):
        multi = MultiLevelDrilldown(
            {'date':[('yearAndMonth', 2, False), ('year', 2, False)]
            }
        )
        drilldown = CallTrace('Drilldown')
        doDrilldownArguments = []
        def doDrilldown(bitMatrixRow, fieldNamesAndMaxResults):
            doDrilldownArguments.append((bitMatrixRow, fieldNamesAndMaxResults))
            self.assertEquals(1, len(fieldNamesAndMaxResults))
            levelField, levelMax, levelSorted = fieldNamesAndMaxResults[0]
            if levelField == 'yearAndMonth':
                raise StopIteration(iter([('yearAndMonth', iter([('2008-01',11),('2008-02',2),('2007-12',1)][:levelMax]))]))
            else:
                raise StopIteration(iter([('year', iter([('2008',13),('2003',10),('2007',10)][:levelMax]))]))
            yield
        drilldown.drilldown = doDrilldown
        multi.addObserver(drilldown)

        result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['date'])))

        self.assertEquals(2, len(doDrilldownArguments))
        self.assertEquals(('bitMatrixRow', [('yearAndMonth', 2, False)]), doDrilldownArguments[0])
        self.assertEquals(('bitMatrixRow', [('year', 2, False)]), doDrilldownArguments[1])
        self.assertEquals(1, len(result))
        (inField, realField), termCounts = result[0]
        self.assertEquals('year', realField)
        self.assertEquals([('2008',13),('2003',10)], list(termCounts))

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
        except MultiLevelDrilldownException, e:
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
            self.assertEquals(1, len(fieldNamesAndMaxResults))
            levelField, levelMax, levelSorted = fieldNamesAndMaxResults[0]
            if levelField == 'yearAndMonth':
                raise StopIteration(iter([('yearAndMonth', iter([('2008-01',11),('2008-02',2),('2007-12',1)][:levelMax]))]))
            else:
                raise StopIteration(iter([('year', iter([]))]))
            yield
        drilldown.drilldown = doDrilldown
        multi.addObserver(drilldown)

        result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['date'])))

        self.assertEquals(2, len(doDrilldownArguments))
        self.assertEquals(('bitMatrixRow', [('yearAndMonth', 2, False)]), doDrilldownArguments[0])
        self.assertEquals(('bitMatrixRow', [('year', 2, False)]), doDrilldownArguments[1])
        self.assertEquals(1, len(result))
        (inField, realField), termCounts = result[0]
        self.assertEquals('yearAndMonth', realField)
        self.assertEquals([('2008-01',11),('2008-02',2)], list(termCounts))

    def testLastZeroReturnValue(self):
        multi = MultiLevelDrilldown(
            {'date':[('yearAndMonth', 2, False), ('year', 2, False)]
            }
        )
        drilldown = CallTrace('Drilldown')
        doDrilldownArguments = []
        def doDrilldown(bitMatrixRow, fieldNamesAndMaxResults):
            doDrilldownArguments.append((bitMatrixRow, fieldNamesAndMaxResults))
            self.assertEquals(1, len(fieldNamesAndMaxResults))
            levelField, levelMax, sorted = fieldNamesAndMaxResults[0]
            if levelField == 'yearAndMonth':
                raise StopIteration(iter([('yearAndMonth', iter([]))]))
            else:
                raise StopIteration(iter([('year', iter([]))]))
            yield
        drilldown.drilldown = doDrilldown
        multi.addObserver(drilldown)

        result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['date'])))

        self.assertEquals(1, len(result))
        (inField, realField), termCounts = result[0]
        self.assertEquals(None, realField)

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
                data = sorted(data, cmp=lambda (term0, card0), (term1, card1): cmp(card1, card0))
            if levelMax > 0:
                data = data[:levelMax]
            raise StopIteration(iter([(levelField, iter(data))]))
            yield
        drilldown.drilldown = doDrilldown

        multi = MultiLevelDrilldown({'date':[('yearAndMonth', 2, False), ('year', 3, True)]})
        multi.addObserver(drilldown)
        result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['date'])))
        self.assertEquals([(('date', 'year'), [('2007', 15), ('2008', 13), ('2003', 10)])], result)

        multi = MultiLevelDrilldown({'date':[('yearAndMonth', 4, False), ('year', 3, False)]})
        multi.addObserver(drilldown)

        result = list(compose(multi.multiLevelDrilldown('bitMatrixRow', ['date'])))
        self.assertEquals([(('date', 'yearAndMonth'), [('2008-01',1),('2008-02',2),('2007-12',11)])], result)



