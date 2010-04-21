## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
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
from cq2utils import CallTrace
from cqlparser import parseString
from merescocomponents.facetindex import CQL2LuceneQuery

class Cql2LuceneQueryTest(TestCase):
    def setUp(self):
        self.convertor = CQL2LuceneQuery({})
        self.convertor.addObserver(CallTrace('Query responder'))
        self.loggedClauses = []
        def logShunt(clause, **kwargs):
            self.loggedClauses.append(clause)
        self.convertor.log = logShunt

    def assertLog(self, expectedClauses, query):
        self.loggedClauses = []
        self.convertor.executeCQL(parseString(query))
        self.assertEquals(expectedClauses, self.loggedClauses)

    def testOneTerm(self):
        self.assertLog(['term'], 'term')

    def testIndexRelationTerm(self):
        self.assertLog(['field = term'], 'field=term')

    def testIndexRelationBoostTerm(self):
        self.assertLog(['field =/boost=1.1 term'], "field =/boost=1.1 term")

    def testIndexExactTerm(self):
        self.assertLog(['field exact term'], 'field exact term')
        self.assertLog(['field exact "term with spaces"'], 'field exact "term with spaces"')

    def testTermAndTerm(self):
        self.assertLog(['term1', 'term2'], 'term1 AND term2')
        self.assertLog(['term1', 'term2', 'term3'], 'term1 AND term2 OR term3')
        self.assertLog(['term1', 'term2', 'term3'], 'term1 AND (term2 OR term3)')
        self.assertLog(['term1', 'term2', 'term3'], 'term1 OR term2 AND term3')

    def testBraces(self):
        self.assertLog(['term'], '(term)')

