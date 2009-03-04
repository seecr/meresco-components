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
from PyLucene import TermQuery, Term, BooleanQuery, BooleanClause, PhraseQuery, LowerCaseFilter, StandardFilter, StandardTokenizer, PrefixQuery
from cqlparser import CqlVisitor, UnsupportedCQL
from StringIO import StringIO
from re import compile

def _analyzeToken(token):
    result = []
    reader = StringIO(unicode(token))
    tokenStream = LowerCaseFilter(StandardFilter(StandardTokenizer(reader)))
    token = tokenStream.next()
    while token:
        result.append(token.termText())
        token = tokenStream.next()
    return result

prefixRegexp = compile(r'^(\w{2,})\*$') # pr*, prefix* ....

def _termOrPhraseQuery(index, termString):
    listOfTermStrings = _analyzeToken(termString.lower())
    if len(listOfTermStrings) == 1:
        if prefixRegexp.match(termString):
            return PrefixQuery(Term(index, listOfTermStrings[0]))
        return TermQuery(Term(index, listOfTermStrings[0]))
    result = PhraseQuery()
    for term in listOfTermStrings:
        result.add(Term(index, term))
    return result

class CqlAst2LuceneVisitor(CqlVisitor):
    def __init__(self, unqualifiedTermFields, node):
        CqlVisitor.__init__(self, node)
        self._unqualifiedTermFields = unqualifiedTermFields

    def visitSCOPED_CLAUSE(self, node):
        clause = CqlVisitor.visitSCOPED_CLAUSE(self, node)
        if len(clause) == 1:
            return clause[0]
        lhs, operator, rhs = clause
        lhsDict = {
            "AND": BooleanClause.Occur.MUST,
            "OR" : BooleanClause.Occur.SHOULD,
            "NOT": BooleanClause.Occur.MUST
        }
        rhsDict = lhsDict.copy()
        rhsDict["NOT"] = BooleanClause.Occur.MUST_NOT
        query = BooleanQuery()
        query.add(lhs, lhsDict[operator])
        query.add(rhs, rhsDict[operator])
        return query

    def visitSEARCH_CLAUSE(self, node):
        results = CqlVisitor.visitSEARCH_CLAUSE(self, node)
        if len(results) == 1:
            (unqualifiedRhs,) = results
            if len(self._unqualifiedTermFields) == 1:
                fieldname, boost = self._unqualifiedTermFields[0]
                query = _termOrPhraseQuery(fieldname, unqualifiedRhs)
                query.setBoost(boost)
            else:
                query = BooleanQuery()
                for fieldname, boost in self._unqualifiedTermFields:
                    subQuery = _termOrPhraseQuery(fieldname, unqualifiedRhs)
                    subQuery.setBoost(boost)
                    query.add(subQuery, BooleanClause.Occur.SHOULD)
            return query
        if len(results) == 3: #either "(" cqlQuery ")" or index relation searchTerm
            ((left,), middle, right) = results
            if left == "(":
                return middle[0]

            relation, boost = middle

            if relation in ['==', 'exact']:
                query = TermQuery(Term(left, right))
            elif relation == '=':
                query = _termOrPhraseQuery(left, right)
            else:
                raise UnsupportedCQL("Only =, == and exact are supported for the field '%s'" % left)

            query.setBoost(boost)
            return query

    def visitRELATION(self, node):
        results = CqlVisitor.visitRELATION(self, node)
        if len(results) == 1:
            relation = results[0]
            boost = 1.0
        else:
            (relation, ((modifier, comparitor, value), )) = results
            boost = float(value)
        return relation, boost


class LuceneQueryComposer:
    def __init__(self, unqualifiedTermFields):
        self._unqualifiedTermFields = unqualifiedTermFields

    def compose(self, node):
        (result,) = CqlAst2LuceneVisitor(self._unqualifiedTermFields, node).visit()
        return result

