# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
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

from merescocomponents.web import WebQuery
from merescocomponents.web.web2cql import _feelsLikePlusMinusQuery, _feelsLikeBooleanQuery
from cqlparser import parseString as parseCql

class Web2CqlTest(TestCase):

    def testQuery(self):
        wq = WebQuery('cats', antiUnaryClause='antiunary')
        self.assertFalse(wq.isBooleanQuery())
        self.assertFalse(wq.isPlusMinusQuery())
        self.assertTrue(wq.isDefaultQuery())
        self.assertFalse(wq.needsBooleanHelp())
        self.assertEquals(parseCql('cats'), wq.ast)
        
    def testPlusMinusQuery(self):
        self.assertPlusMinusQuery('cats', '+cats')
        self.assertPlusMinusQuery('antiunary NOT cats', '-cats')
        self.assertPlusMinusQuery('cats AND dogs', '+cats dogs')
        self.assertPlusMinusQuery('cats NOT dogs', '+cats -dogs')
        self.assertPlusMinusQuery('cats AND dogs', '+cats +dogs')
        self.assertPlusMinusQuery('antiunary NOT cats AND dogs', '-cats dogs')
        self.assertPlusMinusQuery('antiunary NOT cats NOT dogs', '-cats -dogs')
        self.assertPlusMinusQuery('antiunary NOT cats AND dogs', '-cats +dogs')
        self.assertPlusMinusQuery('"cats dogs"', '+"cats dogs"')
        self.assertPlusMinusQuery('"cats dogs" NOT "mice bats"', '+"cats dogs" -"mice bats"')
        self.assertPlusMinusQuery('"cats dogs" NOT label=value', '+"cats dogs" -label=value')
        self.assertPlusMinusQuery('label=value', '+label=value')

    def testDefaultQuery(self):
        self.assertDefaultQuery('cats')
        self.assertDefaultQuery('"-cats"')
        self.assertDefaultQuery('cats AND dogs', 'cats dogs')
        self.assertDefaultQuery('cats AND OR AND dogs AND -fish', 'cats OR dogs -fish', needsBooleanHelp=True)
        self.assertDefaultQuery('"-cats" AND "AND" AND "dogs"', '-cats AND dogs', needsBooleanHelp=True)
        self.assertDefaultQuery('cheese AND "("', 'cheese (', needsBooleanHelp=True)

    def testBooleanQuery(self):
        self.assertBooleanQuery('cats AND dogs')
        self.assertBooleanQuery('cats OR dogs')
        self.assertBooleanQuery('cats NOT dogs')
        self.assertBooleanQuery('cats AND label=value')
        self.assertBooleanQuery('cats AND label="value with spaces"')
        self.assertBooleanQuery('cats NOT (label=value OR label="other value")')
        self.assertBooleanQuery('antiunary NOT cats AND dogs', 'NOT cats AND dogs')
        self.assertBooleanQuery('antiunary NOT ( cats AND dogs )', 'NOT (cats AND dogs)')
        self.assertBooleanQuery('cheese OR ( antiunary NOT mice )', 'cheese OR (NOT mice)')
        self.assertBooleanQuery('"cat treat" AND "dog biscuit"', '"cat treat" and "dog biscuit"')

    def testFeelsLikePlusMinusQuery(self):
        self.assertFalse(_feelsLikePlusMinusQuery('cats OR dogs'))
        self.assertTrue(_feelsLikePlusMinusQuery('cats OR dogs -fish'))
        self.assertFalse(_feelsLikePlusMinusQuery('cats NOT dogs'))
        self.assertTrue(_feelsLikePlusMinusQuery('cats NOT dogs -fish'))
        self.assertTrue(_feelsLikePlusMinusQuery('-cheese ('))
        self.assertFalse(_feelsLikePlusMinusQuery('cheese'))
        self.assertTrue(_feelsLikePlusMinusQuery('(cats) +mice'))
        self.assertTrue(_feelsLikePlusMinusQuery('cats +(dogs -hairy)'))
        self.assertTrue(_feelsLikePlusMinusQuery('-cheese'))
        self.assertTrue(_feelsLikePlusMinusQuery('+cheese -cheddar'))
        self.assertTrue(_feelsLikePlusMinusQuery('+cheese +mouse cat'))
        self.assertTrue(_feelsLikePlusMinusQuery('+cheese'))
        self.assertTrue(_feelsLikePlusMinusQuery('+"cheese"'))
        self.assertFalse(_feelsLikePlusMinusQuery('"+cheese"'))
        self.assertFalse(_feelsLikePlusMinusQuery('"cat +cheese"'))
        self.assertFalse(_feelsLikePlusMinusQuery('label="cat +cheese"'))
        self.assertTrue(_feelsLikePlusMinusQuery('-label="cat +cheese"'))
        
    def testFeelsLikeBooleanQuery(self):
        self.assertTrue(_feelsLikeBooleanQuery('-cats AND dogs'))
        self.assertTrue(_feelsLikeBooleanQuery('"-cats" AND dogs'))
        self.assertFalse(_feelsLikeBooleanQuery('-cats'))
        self.assertTrue(_feelsLikeBooleanQuery('cats OR dogs'))
        self.assertTrue(_feelsLikeBooleanQuery('cats OR dogs -fish'))
        self.assertTrue(_feelsLikeBooleanQuery('cats NOT dogs'))
        self.assertTrue(_feelsLikeBooleanQuery('cats NOT dogs -fish'))
        self.assertTrue(_feelsLikeBooleanQuery('-cheese ('))
        self.assertFalse(_feelsLikeBooleanQuery('cheese'))
        self.assertTrue(_feelsLikeBooleanQuery('(cats) +mice'))
        self.assertTrue(_feelsLikeBooleanQuery('cats +(dogs -hairy)'))
        self.assertFalse(_feelsLikeBooleanQuery('-cheese'))
        self.assertFalse(_feelsLikeBooleanQuery('+cheese -cheddar'))
        self.assertFalse(_feelsLikeBooleanQuery('+cheese +mouse cat'))
        self.assertFalse(_feelsLikeBooleanQuery('"+cheese"'))
        self.assertFalse(_feelsLikeBooleanQuery('"cat +cheese"'))
        self.assertFalse(_feelsLikeBooleanQuery('label="cat +cheese"'))
        self.assertFalse(_feelsLikeBooleanQuery('-label="cat +cheese"'))


    def _assertQuery(self, expected, input, boolean=False, plusminus=False, default=False, needsBooleanHelp=False):
        input = expected if input == None else input
        wq = WebQuery(input, antiUnaryClause='antiunary')
        self.assertEquals((boolean, plusminus, default, needsBooleanHelp), (wq.isBooleanQuery(), wq.isPlusMinusQuery(), wq.isDefaultQuery(), wq.needsBooleanHelp()))
        self.assertEquals(parseCql(expected), wq.ast)
        self.assertEquals(input, wq.original)
        
    def assertDefaultQuery(self, expected, input=None, needsBooleanHelp = False):
        self._assertQuery(expected, input, default=True, needsBooleanHelp=needsBooleanHelp)

    def assertPlusMinusQuery(self, expected, input):
        self._assertQuery(expected, input, plusminus=True)

    def assertBooleanQuery(self, expected, input=None):
        self._assertQuery(expected, input, boolean=True)

    def testReportedProblemWithGoogleLikeQuery(self):
        self.assertDefaultQuery('fiscal AND OR AND "(market" AND "municipalities)"', 'fiscal OR (market municipalities)', needsBooleanHelp=True)
        self.assertBooleanQuery('fiscal OR (market AND municipalities)')
        self.assertBooleanQuery('fiscal OR (market OR municipalities)')
        self.assertBooleanQuery('fiscal OR (market NOT municipalities)')

    def testFilter(self):
        wq = WebQuery('fiets')
        wq.addFilter('field', 'value')
        self.assertCql(parseCql('field exact value AND (fiets)'), wq.ast)

    def testFilterWithSpaces(self):
        wq = WebQuery('fiets')
        wq.addFilter('field', 'value with spaces')
        self.assertEquals(parseCql('field exact "value with spaces" AND (fiets)'), wq.ast)

    def testFilterFilter(self):
        wq = WebQuery('fiets')
        wq.addFilter('field1', 'value1')
        wq.addFilter('field2', 'value2')
        self.assertCql(parseCql('field1 exact value1 AND field2 exact value2 AND (fiets)'), wq.ast)

    def testFilterX4(self):
        wq = WebQuery('fiets')
        wq.addFilter('field1', 'value1')
        wq.addFilter('field2', 'value2')
        wq.addFilter('field3', 'value3')
        wq.addFilter('field4', 'value4')
        self.assertCql(parseCql('field1 exact value1 AND field2 exact value2 AND field3 exact value3 AND field4 exact value4 AND (fiets)'), wq.ast)

    def assertCql(self, expected, input):
        self.assertEquals(expected, input, '%s != %s' %(expected.prettyPrint(), input.prettyPrint()))