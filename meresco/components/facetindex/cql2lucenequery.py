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

from meresco.core import Observable

from meresco.components.statistics import Logger
from meresco.components.facetindex.cqlparsetreetolucenequery import LuceneQueryComposer
from meresco.components.facetindex.clausecollector import ClauseCollector

class CQL2LuceneQuery(Observable, Logger):

    def __init__(self, unqualifiedFields, name=None):
        Observable.__init__(self, name=name)
        self._cqlComposer = LuceneQueryComposer(unqualifiedFields)

    def executeQuery(self, cqlAbstractSyntaxTree, *args, **kwargs):
        return self.asyncany.executeQuery(pyLuceneQuery=self._convert(cqlAbstractSyntaxTree), *args, **kwargs)

    def docsetFromQuery(self, cqlAbstractSyntaxTree, *args, **kwargs):
        return self.any.docsetFromQuery(pyLuceneQuery=self._convert(cqlAbstractSyntaxTree), *args, **kwargs)

    def _convert(self, ast):
        ClauseCollector(ast, self.log).visit()
        return self._cqlComposer.compose(ast)

