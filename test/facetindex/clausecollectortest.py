# -*- coding: utf-8 -*-
from merescocomponents.facetindex import ClauseCollector
from cq2utils import CQ2TestCase
from cqlparser import parseString

class ClauseCollectorTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)

    def testClauseCollector(self):
        self.assertEquals(['cat', 'dog'], self.findClauses("cat or dog"))
        self.assertEquals(['cat', 'dog'], self.findClauses("(cat or dog)"))
        self.assertEquals(['cat', 'dog', 'horse'], self.findClauses("(cat or dog) not horse"))

    def findClauses(self, cql):
        clauses = []
        ClauseCollector(parseString(cql), logger=lambda clause: clauses.append(clause)).visit()
        return clauses

