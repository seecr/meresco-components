# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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

from xmlpump import Converter
from cqlparser.cqlparser import CQLAbstractSyntaxNode
from cqlparser import CqlVisitor

class CQLConversion(Converter):
    def __init__(self, astConversion):
        Converter.__init__(self)
        self._astConversion = astConversion

    def _canConvert(self, anObject):
        return isinstance(anObject, CQLAbstractSyntaxNode)

    def _convert(self, cqlAst):
        return self._astConversion(cqlAst)

class CqlMultiSearchClauseConversion(CQLConversion):
    def __init__(self, filtersAndModifiers):
        CQLConversion.__init__(self, self._convertAst)
        self._filtersAndModifiers = filtersAndModifiers

    def _convertAst(self, ast):
        CqlMultiSearchClauseModification(ast, self._filtersAndModifiers).visit()
        return ast

class CqlSearchClauseConversion(CqlMultiSearchClauseConversion):
    def __init__(self, searchClauseFilter, modifier):
        CqlMultiSearchClauseConversion.__init__(self, [(searchClauseFilter, modifier)])
    
class CqlMultiSearchClauseModification(CqlVisitor):
    def __init__(self, ast, filtersAndModifiers):
        CqlVisitor.__init__(self, ast)
        self._filtersAndModifiers = filtersAndModifiers

    def visitSEARCH_CLAUSE(self, node):
        for searchClauseFilter, searchClauseModifier in self._filtersAndModifiers:
            if searchClauseFilter(node):
                newSearchClause = searchClauseModifier(node)
                assert newSearchClause.name() == 'SEARCH_CLAUSE', 'Expected a SEARCH_CLAUSE'
                node.replaceChildren(*newSearchClause.children())
                return ()
        return CqlVisitor.visitSEARCH_CLAUSE(self, node)

