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
from meresco.framework import Observable
from meresco.components.statistics import Logger
from cqlparsetreetolucenequery import Composer
from clausecollector import ClauseCollector

class CQL2LuceneQuery(Observable, Logger):

    def __init__(self, unqualifiedFields):
        Observable.__init__(self)
        self._cqlComposer = Composer(unqualifiedFields)

    def executeCQL(self, cqlAbstractSyntaxTree, *args, **kwargs):
        ClauseCollector(cqlAbstractSyntaxTree, self.log).visit()
        return self.any.executeQuery(self._cqlComposer.compose(cqlAbstractSyntaxTree), *args, **kwargs)

    def docsetFromQuery(self, cqlAbstractSyntaxTree, *args, **kwargs):
        ClauseCollector(cqlAbstractSyntaxTree, self.log).visit()
        return self.any.docsetFromQuery(self._cqlComposer.compose(cqlAbstractSyntaxTree), *args, **kwargs)
