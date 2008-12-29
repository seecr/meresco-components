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
from facetindex.document import IDFIELD
from PyLucene import QueryFilter, IndexSearcher
from facetindex.docset import DocSet


class Hits(object):

    def __init__(self, searcher, reader, pyLuceneQuery, pyLuceneSort, docIdsMap=None):
        self._reader = reader
        self._searcher = searcher
        self._pyLuceneQuery = pyLuceneQuery
        self._pyLuceneSort = pyLuceneSort
        self._docIdsMap = docIdsMap
        self.hits = self._doQuery()

    def __len__(self):
        return len(self.hits)

    def getDocSet(self):
        return DocSet.fromQuery(self._searcher, self._pyLuceneQuery)

    def __getslice__(self, start, stop):
        return (self[i] for i in xrange(start, min(len(self),stop)))

    def __iter__(self):
        return self[:]

    def __getitem__(self, i):
        return self.hits[i].get(IDFIELD)

    def _doQuery(self):
        if self._pyLuceneSort:
            hits = self._searcher.search(self._pyLuceneQuery, self._pyLuceneSort)
        else:
            hits = self._searcher.search(self._pyLuceneQuery)
        return hits
