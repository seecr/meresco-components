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

from unittest import TestCase
from meresco.components.numeric.numbercomparitormodifier import NumberComparitorModifier
from cqlparser import parseString
from cqlparser.cqlparser import CQL_QUERY, SCOPED_CLAUSE
from meresco.components.numeric import NumberComparitorCqlConversion

class NumberComparitorModifierTest(TestCase):
    def testGTE(self):
        modifier = NumberComparitorModifier('rating', convert=int, valueLength=2)
        sc = parseString('rating >= 23').children()[0].children()[0]
        expected = parseString('(rating.gte exact 3z OR (rating.gte exact 2z AND rating.gte exact z3))')

        self.assertTrue(modifier.canModify(sc))
        self.assertEquals(expected, CQL_QUERY(SCOPED_CLAUSE(modifier.modify(sc))))

    def testOnlyActOnGivenField(self):
        modifier = NumberComparitorModifier('rating', convert=int, valueLength=2)
        sc = parseString('someField >= 23').children()[0].children()[0]

        self.assertFalse(modifier.canModify(sc))

    def testNested(self):
        query = 'field = value AND rating >= 2.3'
        expected = 'field = value AND (rating.gte exact 3z OR (rating.gte exact 2z AND rating.gte exact z3))'
        self.assertAst(expected, query, nrOfDecimals=1)
        
    def assertAst(self, expected, input, fieldname='rating', nrOfDecimals=0, valueLength=2):
        expected = parseString(expected)
        ast = parseString(input)
        self.assertEquals(expected, NumberComparitorCqlConversion(fieldname, nrOfDecimals=nrOfDecimals, valueLength=valueLength)._convertAst(ast))

    def testVerySmallFigures(self):
        query = 'rating < 2'
        self.assertAst('(rating.lte exact 0z AND rating.lte exact z1)', query)
        self.assertAst('(rating.lte exact 0zzz AND (rating.lte exact z0zz AND (rating.lte exact zz0z AND rating.lte exact zzz1)))', query, valueLength=4)

    def testVeryLargeFigures(self):
        modifier = NumberComparitorModifier('rating', convert=int, valueLength=2)
        sc = parseString('rating > 97').children()[0].children()[0]

        expected = parseString('(rating.gte exact 9z AND rating.gte exact z8)')
        self.assertEquals(expected, CQL_QUERY(SCOPED_CLAUSE(modifier.modify(sc))))


    def testLessThanZero(self):
        self.assertAst('rating.lte exact zz', 'rating < 0')
        self.assertAst('rating.lte exact zz', 'rating < -10')

    def testGreaterThanMax(self):
        self.assertAst('rating.gte exact zz', 'rating > 99')
        self.assertAst('rating.gte exact zz', 'rating >= 2399')

        
