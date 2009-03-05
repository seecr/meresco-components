#-*- coding: utf-8
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
from unittest import TestCase
from cq2utils import CallTrace
from cqlparser import parseString
from merescocomponents.cqlsuggester import CqlSuggester
from merescocomponents.ngram import LevenshteinSuggester


class MockIndex(object):
    def __init__(self, results):
        self._results = results
    def executeQuery(self, query, maxResult):
        return len(self._results), self._results

class CqlSuggesterTest(TestCase):

    def testTwoWords(self):
        suggester = CallTrace('suggester')
        def suggestionsFor(term):
            return ['wordy']
        suggester.suggestionsFor = suggestionsFor
        cqlquery = parseString('word0 and word1')
        cqlsuggester = CqlSuggester()
        cqlsuggester.addObserver(suggester)
        result = cqlsuggester.suggestForCql(cqlAST=cqlquery)
        self.assertEquals(['wordy'], result)

    def testTwoWordsWithRealSuggester(self) :
        index = MockIndex(['wordy', 'wordx'])
        self.assertEquals((2, ['wordy', 'wordx']), index.executeQuery('nonsense', 99))
        suggester = LevenshteinSuggester(samples=50, threshold=10, maxResults=5)
        suggester.addObserver(index)
        self.assertEquals((False, ['wordy', 'wordx']), suggester.suggestionsFor('wordz'))
        self.assertEquals((True, ['wordx']), suggester.suggestionsFor('wordy'))
        cqlsuggester = CqlSuggester()
        cqlsuggester.addObserver(suggester)
        cqlAST = parseString('wordz and wordy')
        self.assertEquals('wordz', cqlAST.children()[0].children()[0].children()[0].children()[0].children()[0])
        result = cqlsuggester.suggestForCql(cqlAST)
        self.assertEquals((False, ['wordy', 'wordx']), result)



