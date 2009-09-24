# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
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

from merescocore.framework import Observable
from itertools import islice
from ngram import ngrams, NGRAMS_FIELD, NAME_FIELD, NAME_TEMPLATE
from merescocomponents.facetindex.merescolucene import BooleanQuery, BooleanClause, TermQuery, Term, Query

BooleanClause_Occur_MUST = BooleanClause.Occur.MUST
BooleanClause_Occur_SHOULD = BooleanClause.Occur.SHOULD

class NGramQuery(Observable):
    def __init__(self, N=2, fieldnames=None, samples=50, fieldForSorting=None):
        Observable.__init__(self)
        self._fieldnames = fieldnames if fieldnames != None else []
        self._N = N
        self._samples = samples
        self._fieldForSorting = fieldForSorting

    def executeNGramQuery(self, query, maxResults, fieldname=None):
        total, recordIds =  self.any.executeQuery(self.ngramQuery(query, fieldname=fieldname), start=0, stop=self._samples)
        sortedRecordIds = recordIds
        if self._fieldForSorting and maxResults < total and maxResults < self._samples:
            sortedRecordIds = sorted(recordIds, key=self._wordCardinality, reverse=True)
        return islice((word.rsplit('$', 1)[0] for word in sortedRecordIds), maxResults)

    def _wordCardinality(self, word):
        return self.any.docsetlist(self._fieldForSorting).cardinality(word.rsplit('$', 1)[0])

    def ngramQuery(self, word, fieldname=None):
        """Construct a query for the given word using a word-distance of self._N"""
        combinedquery = BooleanQuery()
        combinedquery.add(BooleanClause(
            TermQuery(
                Term(
                    NAME_FIELD,
                    NAME_TEMPLATE % (fieldname if fieldname in self._fieldnames else '')
                )
            ) % Query,
            BooleanClause_Occur_MUST))
        query = BooleanQuery()
        combinedquery.add(query % Query, BooleanClause_Occur_MUST)
        for ngram in ngrams(word, self._N):
            query.add(BooleanClause(TermQuery(Term(NGRAMS_FIELD, ngram)) % Query, BooleanClause_Occur_SHOULD))
        return combinedquery
