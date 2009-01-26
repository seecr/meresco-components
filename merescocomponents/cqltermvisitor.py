## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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

from cqlparser import CqlVisitor

class CqlTermVisitor(CqlVisitor) :
    def visitSCOPED_CLAUSE(self, node):
        clause = CqlVisitor.visitSCOPED_CLAUSE(self, node)
        if len(clause) == 1:
            return clause[0]
        lhs, operator, rhs = clause
        return lhs + rhs

    def visitSEARCH_CLAUSE(self, node):
        results = CqlVisitor.visitSEARCH_CLAUSE(self, node)
        if len(results) == 1:
            return results[0]
        if len(results) == 3: #either "(" cqlQuery ")" or index relation searchTerm
            ((left,), middle, right) = results
            if left == "(":
                return middle
        return []

    def visitCQL_QUERY(self, node):
        return CqlVisitor.visitCQL_QUERY(self, node)[0]

    def visitTERM(self, node):
        return [CqlVisitor.visitTERM(self, node)]

def getAllTerms(cqlAST):
    return CqlTermVisitor(cqlAST).visit()