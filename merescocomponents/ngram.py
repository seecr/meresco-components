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

from merescocore.framework import Transparant,  Observable
from merescocomponents.facetindex import document
from PyLucene import BooleanQuery, BooleanClause, TermQuery, Term
from Levenshtein import distance, ratio
from itertools import islice

def ngrams(word, N=2):
    word = unicode(word)
    for n in range(2, N+1):
        for i in range(len(word)-n+1):
            yield word[i:i+n]

class NGramQuery(Observable):
    def __init__(self, n, fieldName):
        Observable.__init__(self)
        self._fieldName = fieldName

    def executeQuery(self, query, samples):
        return self.any.executeQuery(self.ngramQuery(query), start=0, stop=samples)

    def ngramQuery(self, word, N=2):
        """Construct a query for the given word using a word-distance of N
        (default: 2)
        """
        query = BooleanQuery()
        for ngram in ngrams(word, N):
            query.add(BooleanClause(TermQuery(Term(self._fieldName, ngram)), BooleanClause.Occur.SHOULD))
        return query

class _Suggestion(Observable):
    def __init__(self, samples, threshold, maxResults):
        """Create a Suggestion object providing the boundaries used by the
        subclasses.
        """
        Observable.__init__(self)
        self._samples = samples
        self._maxResults = maxResults
        self._threshold = threshold

    def _suggestionsFor(self, word, sortkey):
        """Query the given word and (re)sort the result using the
        subclass-specific algorithm.
        The  initial result of the query is limited to the predefined number
        of samples. These results are inputted into the subclass-specific
        algorithm and the result is limited to a predefined maximum.
        """
        total, candidates = self.any.executeQuery(word, self._samples)
        results = sorted(candidates, key=sortkey)
        inclusive = results and results[0] == word
        if inclusive:
            return (inclusive, results[1:self._maxResults+1])
        else:
            return (inclusive, results[:self._maxResults])

class LevenshteinSuggester(_Suggestion):
    def suggestionsFor(self, word):
        """Return suggestions for the given word using the absolute Levenshtein
        distance of two strings.

        If the ratio between the given word and found term is less or equal to
        the predefined threshold, the term is added to the result.

        (see http://en.wikipedia.org/wiki/Levenshtein_distance for details).
        """
        word = unicode(word)
        inclusive, result = self._suggestionsFor(word, lambda term: distance(unicode(term), word))
        return inclusive, [term for term in result if distance(unicode(term), word) <= self._threshold]

class RatioSuggester(_Suggestion):
    def suggestionsFor(self, word):
        """Return suggestions for the given word by computing the similarity
        of two strings.

        If the ratio between the given word and found term exceeds the
        predefined threshold, the term is added to the result.

        (see http://en.wikipedia.org/wiki/Levenshtein_distance for details).
        """
        word = unicode(word)
        inclusive, result = self._suggestionsFor(word, lambda term: 1-ratio(unicode(term), word))
        return inclusive, [term for term in result if ratio(unicode(term), word) > self._threshold]

class NGramFieldlet(Transparant):
    """Fieldlet used in Meresco DNA to build/fill an NGram index used for
    suggestions."""
    def __init__(self, n, fieldName):
        Transparant.__init__(self)
        self._fieldName = fieldName
        self._ngram = lambda word:ngrams(word, n)

    def addField(self, name, value):
        for word in unicode(value).split():
            count, ids = self.any.executeQuery(TermQuery(Term(document.IDFIELD, word)))
            if count > 0:
                continue

            self.ctx.tx.locals['id'] = word
            ngrams = ' '.join(self._ngram(word))
            self.do.addField(self._fieldName, ngrams)
            #for ngram in self._ngram(word):
                #self.do.addField(self._fieldName, ngram)

