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

from merescocore.framework import Observable

from merescocomponents.web.googlelikeparse import unGoogleQuery, isGoogleLikeQuery, isGoogleLikePlusMinusQuery, isGoogleLikeBooleanQuery, _joinFieldAndTerm

class GoogleLikeParseTest(TestCase):

    def testGoogleLikeQueryDetection(self):
        self.assertFalse(isGoogleLikeQuery('cats dogs'))
        self.assertTrue(isGoogleLikeQuery('cats and dogs'))
        self.assertFalse(isGoogleLikeQuery('cats'))
        self.assertTrue(isGoogleLikeQuery('-cats'))
        self.assertFalse(isGoogleLikeQuery('ca-ts'))
        self.assertFalse(isGoogleLikeQuery('cats-'))
        self.assertFalse(isGoogleLikeQuery('(cats)'))
        self.assertFalse(isGoogleLikeQuery('('))
        self.assertTrue(isGoogleLikeQuery('+cats'))

    def testUnGoogleQueryBoolean(self):
        self.assertEquals('antiunary NOT cats AND dogs', unGoogleQuery('NOT cats AND dogs', antiUnaryClause="antiunary"))
        self.assertEquals('antiunary NOT ( cats AND dogs )', unGoogleQuery('NOT (cats AND dogs)', antiUnaryClause="antiunary"))
        self.assertEquals('cheese OR ( antiunary NOT mice )', unGoogleQuery('cheese OR (NOT mice)', antiUnaryClause="antiunary"))
        self.assertEquals('"cat treat" AND "dog biscuit"', unGoogleQuery('"cat treat" and "dog biscuit"', antiUnaryClause="antiunary") )

    def testUnGoogleQueryPlusMinus(self):
        self.assertEquals('(antiunary NOT cats)', unGoogleQuery('-cats', antiUnaryClause="antiunary"))
        self.assertEquals('(dogs NOT cats)', unGoogleQuery('dogs -cats'))
        self.assertEquals('cats', unGoogleQuery('+cats', antiUnaryClause="antiunary"))
        self.assertEquals('cats AND dogs', unGoogleQuery('+cats +dogs', antiUnaryClause="antiunary"))
        self.assertEquals('(antiunary NOT cats) AND dogs', unGoogleQuery('-cats +dogs', antiUnaryClause="antiunary"))
        self.assertEquals('(cats NOT dogs)', unGoogleQuery('+cats -dogs', antiUnaryClause="antiunary"))
        self.assertEquals('((cats NOT dogs) NOT mice)', unGoogleQuery('+cats -dogs -mice', antiUnaryClause="antiunary"))
        self.assertEquals('cats AND dogs', unGoogleQuery('+cats dogs', antiUnaryClause="antiunary"))

        self.assertEquals('"cat treat" AND "dog biscuit"', unGoogleQuery('+"cat treat" +"dog biscuit"', antiUnaryClause="antiunary") )
        self.assertEquals('(antiunary NOT "cat treat")', unGoogleQuery('-"cat treat"', antiUnaryClause="antiunary") )
        self.assertEquals('("cat treat" NOT "dog biscuit")', unGoogleQuery('+"cat treat" -"dog biscuit"', antiUnaryClause="antiunary") )

    def testIsGoogleLikePlusMinusQuery(self):
        self.assertTrue(isGoogleLikePlusMinusQuery('+cats'))
        self.assertTrue(isGoogleLikePlusMinusQuery('-cats'))
        self.assertTrue(isGoogleLikePlusMinusQuery('+cats dogs'))
        self.assertTrue(isGoogleLikePlusMinusQuery('+cats -dogs'))
        self.assertTrue(isGoogleLikePlusMinusQuery('+cats +dogs'))
        self.assertTrue(isGoogleLikePlusMinusQuery('-cats dogs'))
        self.assertTrue(isGoogleLikePlusMinusQuery('-cats -dogs'))
        self.assertTrue(isGoogleLikePlusMinusQuery('-cats +dogs'))
        self.assertTrue(isGoogleLikePlusMinusQuery('+"cats dogs"'))
        self.assertTrue(isGoogleLikePlusMinusQuery('+"cats dogs" -"mice bats"'))
        
        self.assertFalse(isGoogleLikePlusMinusQuery('cats'))
        self.assertFalse(isGoogleLikePlusMinusQuery('"-cats"'))
        self.assertFalse(isGoogleLikePlusMinusQuery('cats dogs'))
        self.assertFalse(isGoogleLikePlusMinusQuery('-cats AND dogs'))
        self.assertFalse(isGoogleLikePlusMinusQuery('cats OR dogs'))
        self.assertFalse(isGoogleLikePlusMinusQuery('cats OR dogs -fish'))
        self.assertFalse(isGoogleLikePlusMinusQuery('cats NOT dogs'))
        self.assertFalse(isGoogleLikePlusMinusQuery('cats NOT dogs -fish'))
        
        self.assertFalse(isGoogleLikePlusMinusQuery('-cheese ('))
        self.assertFalse(isGoogleLikePlusMinusQuery('(cats) +mice'))
        self.assertFalse(isGoogleLikePlusMinusQuery('cats +(dogs -hairy)'))

    def testIsGoogleLikeBooleanQuery(self):
        self.assertTrue(isGoogleLikeBooleanQuery('cats AND dogs'))
        self.assertTrue(isGoogleLikeBooleanQuery('cats OR dogs'))
        self.assertTrue(isGoogleLikeBooleanQuery('cats NOT dogs'))
        self.assertTrue(isGoogleLikeBooleanQuery('"cats treat" AND "dog biscuit"'))
        
        self.assertFalse(isGoogleLikeBooleanQuery('+cats'))
        self.assertFalse(isGoogleLikeBooleanQuery('cats -dogs'))
        
        self.assertFalse(isGoogleLikeBooleanQuery('cats AND -dogs'))
        self.assertFalse(isGoogleLikeBooleanQuery('+cats AND +dogs'))
        self.assertFalse(isGoogleLikeBooleanQuery('(cats)'))
        self.assertFalse(isGoogleLikeBooleanQuery('(cats dogs)'))

    def testJoinFieldAndTerm(self):
        self.assertEquals("field exact value", _joinFieldAndTerm(['field:value']))
        self.assertEquals("(field1 exact value1) AND (field2 exact value2)", _joinFieldAndTerm(['field1:value1', 'field2:value2']))
        self.assertEquals('field exact "word1 word2"', _joinFieldAndTerm(['field:word1 word2']))

    def testReportedProblemWithGoogleLikeQuery(self):
        self.assertTrue(isGoogleLikeQuery('fiscal OR (market municipalities)'))
        self.assertTrue(isGoogleLikeQuery('fiscal OR (market AND municipalities)'))
        self.assertTrue(isGoogleLikeQuery('fiscal OR (market OR municipalities)'))
        self.assertTrue(isGoogleLikeQuery('fiscal OR (market NOT municipalities)'))


