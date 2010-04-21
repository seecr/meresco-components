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

from cqlparser import CqlVisitor

class RenameCqlIndex(object):
    def __init__(self, fieldRename):
        self._fieldRename = fieldRename

    def __call__(self, cqlAst):
        _CqlIndexChangeVisitor(self._fieldRename, cqlAst).visit()
        return cqlAst

class _CqlIndexChangeVisitor(CqlVisitor):
    def __init__(self, fieldRename, root):
        CqlVisitor.__init__(self, root)
        self._fieldRename = fieldRename

    def visitINDEX(self, node):
        #INDEX(TERM('term'))
        assert len(node.children()) == 1
        term = node.children()[0]
        termString = term.children()[0]
        term.replaceChildren(self._fieldRename(termString))
        return node
