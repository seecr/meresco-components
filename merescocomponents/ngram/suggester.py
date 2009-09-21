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

from itertools import islice
from merescocore.framework import Observable
from Levenshtein import distance, ratio

class _Suggestion(Observable):
    def __init__(self, samples, threshold, maxResults):
        """Create a Suggestion object providing the boundaries used by the
        subclasses.
        """
        Observable.__init__(self)
        self._samples = samples
        self._threshold = threshold
        self._maxResults = maxResults

    def suggestionsFor(self, wordAsUtf8, fieldnameAsUtf8=None):
        """Query the given word and (re)sort the result using the
        subclass-specific algorithm.
        The  initial result of the query is limited to the predefined number
        of samples. These results are inputted into the subclass-specific
        algorithm and the result is limited to a predefined maximum.
        """
        word = unicode(wordAsUtf8)
        fieldname = unicode(fieldnameAsUtf8) if fieldnameAsUtf8 else None
        candidates = self.any.executeNGramQuery(word, self._samples, fieldname=fieldname)
        results = sorted(candidates, key=lambda term: self.sortKey(term, word, fieldname))

        inclusive = 1 if results and results[0] == word else 0
        result = islice(results, inclusive, self._maxResults + inclusive)
        return bool(inclusive), [str(term) for term in result if self.threshold(term, word, fieldname)]

class LevenshteinSuggester(_Suggestion):
    """ (see http://en.wikipedia.org/wiki/Levenshtein_distance for details). """

    def sortKey(self, term, word, fieldname):
        return distance(term, word)

    def threshold(self, term, word, fieldname):
        return distance(term, word) <= self._threshold

class RatioSuggester(_Suggestion):
    """ (see http://en.wikipedia.org/wiki/Levenshtein_distance for details). """

    def sortKey(self, word, term, fieldname):
        return 1-ratio(term, word)

    def threshold(self, word, term, fieldname):
        return ratio(term, word) > self._threshold
