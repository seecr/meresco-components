## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from cqlparser import CqlVisitor

class ClauseCollector(CqlVisitor):

    def __init__(self, astTree, logger):
        CqlVisitor.__init__(self, astTree)
        self._logger = logger

    def visitSEARCH_CLAUSE(self, node):
        firstChild = node.children[0].name
        result = CqlVisitor.visitSEARCH_CLAUSE(self, node)
        if firstChild == 'SEARCH_TERM':
            self._logger(clause = result[0].lower())
        elif firstChild == 'INDEX':
            self._logger(clause = "%s %s %s" % (result[0], result[1], quot(result[2].lower())))
        return result

    def visitRELATION(self, node):
        result = CqlVisitor.visitRELATION(self, node)
        if len(result) == 1:
            return result[0]
        relation, (modifier, comparitor, value) = result
        return "%s/%s%s%s" % (relation, modifier, comparitor, value)

def quot(aString):
    if ' ' in aString:
        return '"%s"' % aString
    return aString
