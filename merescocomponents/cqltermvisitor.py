
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