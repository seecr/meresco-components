# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2012, 2015, 2017-2018, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2015, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2017, 2020 SURF https://www.surf.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from unittest import TestCase

from meresco.components.web import WebQuery
from meresco.components.web.webquery import _feelsLikePlusMinusQuery, _feelsLikeBooleanQuery
from cqlparser import parseString as parseCql, cqlToExpression

class WebQueryTest(TestCase):

    def testQuery(self):
        wq = WebQuery('cats', antiUnaryClause='antiunary exact true')
        self.assertFalse(wq.isBooleanQuery())
        self.assertFalse(wq.isPlusMinusQuery())
        self.assertTrue(wq.isDefaultQuery())
        self.assertFalse(wq.needsBooleanHelp())
        self.assertEqual(parseCql('cats'), wq.ast)

    def testCqlQuery(self):
        self.assertEqual(cqlToExpression('field = value'), WebQuery('field=value').query)
        self.assertTrue(WebQuery('field = value').isDefaultQuery())
        self.assertFalse(WebQuery('field = value').isBooleanQuery())
        self.assertFalse(WebQuery('field = value').isPlusMinusQuery())
        self.assertEqual(cqlToExpression('field = value'), WebQuery('field = value').query)
        self.assertEqual(cqlToExpression('field exact value'), WebQuery('field exact value').query)

    def testPlusMinusQuery(self):
        self.assertPlusMinusQuery('cats', '+cats')
        self.assertPlusMinusQuery('antiunary exact true NOT cats', '-cats')
        self.assertPlusMinusQuery('cats AND dogs', '+cats dogs')
        self.assertPlusMinusQuery('cats NOT dogs', '+cats -dogs')
        self.assertPlusMinusQuery('cats AND dogs', '+cats +dogs')
        self.assertPlusMinusQuery('antiunary exact true NOT cats AND dogs', '-cats dogs')
        self.assertPlusMinusQuery('antiunary exact true NOT cats NOT dogs', '-cats -dogs')
        self.assertPlusMinusQuery('antiunary exact true NOT cats AND dogs', '-cats +dogs')
        self.assertPlusMinusQuery('"cats dogs"', '+"cats dogs"')
        self.assertPlusMinusQuery('"cats dogs" NOT "mice bats"', '+"cats dogs" -"mice bats"')
        self.assertPlusMinusQuery('"cats dogs" NOT label=value', '+"cats dogs" -label=value')
        self.assertPlusMinusQuery('label=value', '+label=value')

    def testDefaultQuery(self):
        self.assertDefaultQuery('cats')
        self.assertDefaultQuery('"cats dogs mice"')
        self.assertDefaultQuery('"-cats"', asString='-cats')
        self.assertDefaultQuery('cats AND dogs', 'cats dogs')
        self.assertDefaultQuery('cats AND OR AND dogs AND -fish', 'cats OR dogs -fish', needsBooleanHelp=True)
        self.assertDefaultQuery('-cats AND dogs', '-cats AND dogs', needsBooleanHelp=True, asString='-cats AND dogs')
        self.assertDefaultQuery('cheese AND "("', 'cheese (', needsBooleanHelp=True)
        self.assertDefaultQuery('antiunary exact true', '')
        self.assertDefaultQuery('label=value')
        self.assertDefaultQuery('label="value value"')
        self.assertDefaultQuery('water AND "+(rain" AND "-snow)"', 'water +(rain -snow)', needsBooleanHelp=True)
        self.assertDefaultQuery('water AND "+(rain" AND or AND "snow)"', 'water +(rain or snow)', needsBooleanHelp=True)

    def testParseErrorsWithMinusSign(self):
        self.assertDefaultQuery('-')
        self.assertDefaultQuery('- AND -', '- -')
        self.assertDefaultQuery('- AND +', '- +')
        self.assertDefaultQuery('-+-')

        self.assertDefaultQuery('cats AND - AND dogs', 'cats - dogs')

    def testBooleanQuery(self):
        self.assertBooleanQuery('cats AND dogs')
        self.assertBooleanQuery('cats OR dogs')
        self.assertBooleanQuery('cats NOT dogs')
        self.assertBooleanQuery('cats AND label=value')
        self.assertBooleanQuery('cats AND label="value with spaces"')
        self.assertBooleanQuery('cats NOT (label=value OR label="other value")')
        self.assertBooleanQuery('antiunary exact true NOT cats AND dogs', 'NOT cats AND dogs')
        self.assertBooleanQuery('antiunary exact true NOT (cats AND dogs)', 'NOT (cats AND dogs)')
        self.assertBooleanQuery('cheese OR (antiunary exact true NOT mice)', 'cheese OR (NOT mice)')
        self.assertBooleanQuery('"cat treat" AND "dog biscuit"', '"cat treat" and "dog biscuit"')
        self.assertBooleanQuery('((fiets) AND (onderzoek)) AND meta.repository.collection exact hbokennisbank')

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
        self.assertTrue(_feelsLikePlusMinusQuery('water +(rain or snow)'))

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
        self.assertTrue(_feelsLikeBooleanQuery('water +(rain or snow)'))

    def _assertQuery(self, expected, input, boolean=False, plusminus=False, default=False, needsBooleanHelp=False, asString=None):
        input = expected if input == None else input
        asString = expected if asString == None else asString
        wq = WebQuery(input, antiUnaryClause='antiunary exact true')
        self.assertEqual((boolean, plusminus, default, needsBooleanHelp), (wq.isBooleanQuery(), wq.isPlusMinusQuery(), wq.isDefaultQuery(), wq.needsBooleanHelp()))
        self.assertEqual(parseCql(expected), wq.ast)
        self.assertEqual(cqlToExpression(expected), wq.query)
        self.assertEqual(asString, wq.asString())
        self.assertEqual(input, wq.original)

    def assertDefaultQuery(self, expected, input=None, needsBooleanHelp = False, asString=None):
        self._assertQuery(expected, input, default=True, needsBooleanHelp=needsBooleanHelp, asString=asString)

    def assertPlusMinusQuery(self, expected, input, asString=None):
        self._assertQuery(expected, input, plusminus=True, asString=asString)

    def assertBooleanQuery(self, expected, input=None, asString=None):
        self._assertQuery(expected, input, boolean=True, asString=asString)

    def testReportedProblemWithGoogleLikeQuery(self):
        self.assertDefaultQuery('fiscal AND OR AND "(market" AND "municipalities)"', 'fiscal OR (market municipalities)', needsBooleanHelp=True)
        self.assertBooleanQuery('fiscal OR (market AND municipalities)')
        self.assertBooleanQuery('fiscal OR (market OR municipalities)')
        self.assertBooleanQuery('fiscal OR (market NOT municipalities)')

    def testFilter(self):
        wq = WebQuery('fiets')
        wq.addFilter('field', 'value')
        self.assertCql(parseCql('(fiets) AND field exact value'), wq.ast)

    def testTermFilter(self):
        wq = WebQuery('fiets')
        wq.addTermFilter("water")
        #self.assertCql(parseCql('water AND (fiets)'), wq.ast)
        self.assertCql(parseCql('(fiets) AND water'), wq.ast)

    def testFilterWithSpaces(self):
        wq = WebQuery('fiets')
        wq.addFilter('field', 'value with spaces')
        self.assertCql(parseCql('(fiets) AND field exact "value with spaces"'), wq.ast)

    def testFilterFilter(self):
        wq = WebQuery('fiets')
        wq.addFilter('field1', 'value1')
        wq.addFilter('field2', 'value2')
        self.assertCql(parseCql('(fiets) AND field1 exact value1 AND field2 exact value2'), wq.ast)

    def testFilterX4(self):
        wq = WebQuery('fiets')
        wq.addFilter('field1', 'value1')
        wq.addFilter('field2', 'value2')
        wq.addFilter('field3', 'value3')
        wq.addFilter('field4', 'value4')
        self.assertCql(parseCql('(fiets) AND field1 exact value1 AND field2 exact value2 AND field3 exact value3 AND field4 exact value4'), wq.ast)

    def testReplaceTerm(self):
        wq = WebQuery('fiets')
        newWq = wq.replaceTerm('fiets', 'bike')
        self.assertEqual('fiets', wq.original)
        self.assertEqual('bike', newWq.original)

    def testReplaceTermOnLabelQuery(self):
        wq = WebQuery('transport=fiets')
        newWq = wq.replaceTerm('fiets', 'bike')
        self.assertEqual('transport=bike', newWq.original)
    
    def testReplaceIndex(self):
        wq = WebQuery('transport=fiets')
        newWq = wq.replaceIndex(dict(transport="vervoer"))
        self.assertEqual('vervoer=fiets', newWq.original)

    def testReplaceTerms(self):
        wq = WebQuery('fiets kaart')
        newWq = wq.replaceTerm('fiets', 'bike')
        self.assertEqual('fiets kaart', wq.original)
        self.assertEqual('bike AND kaart', newWq.original)

    def testReplaceTermsWithFilters(self):
        wq = WebQuery('fiets kaart')
        wq.addFilter('label', 'value')
        newWq = wq.replaceTerm('fiets', 'bike')
        self.assertEqual('fiets kaart', wq.original)
        self.assertEqual('bike AND kaart', newWq.original)
        self.assertCql(parseCql('(bike AND kaart) AND label exact value'), newWq.ast)

    def testHasFilters(self):
        wq = WebQuery('fiets kaart')
        self.assertFalse(wq.hasFilters())
        wq.addFilter('label', 'value')
        self.assertTrue(wq.hasFilters())

        wq = WebQuery('fiets kaart')
        self.assertFalse(wq.hasFilters())
        wq.addTermFilter("water")
        self.assertTrue(wq.hasFilters())

    def assertCql(self, expected, input):
        self.assertEqual(expected, input, '%s != %s' %(expected.prettyPrint(), input.prettyPrint()))

    def testError(self):
        wq = WebQuery('\'"a')
        self.assertCql(parseCql('"\'" AND "a"'), wq.ast)
        wq = WebQuery('<?xml version="1.0" encoding="ISO-8859-1"?>\n<!DOCTYPE foo [\n<!ELEMENT foo ANY >\n<!ENTITY xxe SYSTEM "file:///etc/passwd" >]><foo>&xxe;</foo>')
        self.assertCql(parseCql('"<?xml version=\\"1.0\\" encoding=\\"ISO-8859-1\\"?>\n<!DOCTYPE foo [\n<!ELEMENT foo ANY >\n<!ENTITY xxe SYSTEM \\"file:///etc/passwd\\" >]><foo>&xxe;</foo>"'), wq.ast)
