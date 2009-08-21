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
from Levenshtein import distance, ratio

class _Suggestion(Observable):
    def __init__(self, samples, threshold, maxResults):
        """Create a Suggestion object providing the boundaries used by the
        subclasses.
        """
        Observable.__init__(self)
        self._samples = samples
        self._maxResults = maxResults
        self._threshold = threshold

    def _suggestionsFor(self, word, sortkey, fieldname=None):
        """Query the given word and (re)sort the result using the
        subclass-specific algorithm.
        The  initial result of the query is limited to the predefined number
        of samples. These results are inputted into the subclass-specific
        algorithm and the result is limited to a predefined maximum.
        """

        total, candidates = self.any.executeNGramQuery(word, self._samples, fieldname=fieldname)

        results = sorted(candidates, key=sortkey)
        inclusive = results and results[0] == word
        if inclusive:
            return (inclusive, results[1:self._maxResults+1])
        else:
            return (inclusive, results[:self._maxResults])

class LevenshteinSuggester(_Suggestion):
    def suggestionsFor(self, word, fieldname=None):
        """Return suggestions for the given word using the absolute Levenshtein
        distance of two strings.

        If the ratio between the given word and found term is less or equal to
        the predefined threshold, the term is added to the result.

        (see http://en.wikipedia.org/wiki/Levenshtein_distance for details).
        """
        word = unicode(word)
        inclusive, result = self._suggestionsFor(word, lambda term: distance(unicode(term), word), fieldname=fieldname)
        return inclusive, [term for term in result if distance(unicode(term), word) <= self._threshold]

class RatioSuggester(_Suggestion):
    def suggestionsFor(self, word, fieldname=None):
        """Return suggestions for the given word by computing the similarity
        of two strings.

        If the ratio between the given word and found term exceeds the
        predefined threshold, the term is added to the result.

        (see http://en.wikipedia.org/wiki/Levenshtein_distance for details).
        """
        word = unicode(word)
        inclusive, result = self._suggestionsFor(word, lambda term: 1-ratio(unicode(term), word), fieldname=fieldname)
        return inclusive, [term for term in result if ratio(unicode(term), word) > self._threshold]
