## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from cqlparser.cqlparser import RELATION, SEARCH_CLAUSE, CQL_QUERY, INDEX, COMPARITOR, SEARCH_TERM, TERM, BOOLEAN, SCOPED_CLAUSE
from util import Util

from meresco.components import CqlSearchClauseConversion
from convert import Convert

def filterAndModifier(fieldname, nrOfDecimals, valueLength):
    modifier = NumberComparitorModifier(fieldname=fieldname, convert=Convert(nrOfDecimals), valueLength=valueLength)
    return modifier.canModify, modifier.modify

def NumberComparitorCqlConversion(fieldname, nrOfDecimals, valueLength):
    return CqlSearchClauseConversion(*filterAndModifier(fieldname, nrOfDecimals, valueLength))

class NumberComparitorModifier(object):
    def __init__(self, fieldname, convert, valueLength):
        self._fieldname = fieldname
        self._convert = convert
        self._util = Util(valueLength)

    def canModify(self, node):
        #SEARCH_CLAUSE(INDEX(TERM('term')),RELATION(COMPARITOR('...')),SEARCH_TERM(...))
        return node.children()[0].name() == 'INDEX' and \
              node.children()[0].children()[0].children()[0] == self._fieldname and \
              node.children()[1].children()[0].children()[0] in ['>=', '<', '>',  '<=']

    def modify(self, node):
        comparitor = node.children()[1].children()[0].children()[0]
        value = node.children()[2].children()[0].children()[0]

        field = "%s.gte" % self._fieldname if ">" in comparitor else "%s.lte" % self._fieldname
        higherInOrdering = 1 if ">" in comparitor else -1

        value = self._convert(value)

        if not '=' in comparitor:
            value = value + higherInOrdering

        if (value < 0 and '<' in comparitor) or \
            (value >= self._util.maximum and '>' in comparitor):
                return self._simpleSearchClause(field, 'z' * self._util.valueLength)
        value = max(min(value, self._util.maximum - 1), 0)

        return self._searchClause(self._util.valueLength - 1, value, higherInOrdering, field)

    def _searchClause(self, decimalPosition, value, higherInOrdering, field):
        if decimalPosition == 0:
            return self._simpleSearchClause(field, self._util.termForPosition(value, decimalPosition))
        else:
            decimal = self._util.decimal(value, decimalPosition)
            nestedClause =  SEARCH_CLAUSE(
                CQL_QUERY(
                    SCOPED_CLAUSE(
                        self._simpleSearchClause(field, self._util.termWithDecimal(decimal, decimalPosition)),
                        BOOLEAN('and'),
                        SCOPED_CLAUSE(
                            self._searchClause(decimalPosition -1, value, higherInOrdering, field)
                        )
                    )
                ),
            )
            if decimal + higherInOrdering < 0:
                return nestedClause
            if decimal + higherInOrdering == self._util.base:
                return nestedClause
            return SEARCH_CLAUSE(
                CQL_QUERY(
                    SCOPED_CLAUSE(
                        self._simpleSearchClause(field, self._util.termWithDecimal(decimal + higherInOrdering, decimalPosition)),
                        BOOLEAN('or'),
                        SCOPED_CLAUSE(
                            nestedClause
                        )
                    )
                ),
            )

    def _simpleSearchClause(self, field, aString):
        return SEARCH_CLAUSE(
            INDEX(TERM(field)),
            RELATION(COMPARITOR('exact')),
            SEARCH_TERM(TERM(aString))
        )

