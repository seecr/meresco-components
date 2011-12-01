#-*- coding: utf-8
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
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

from unittest import TestCase
from cq2utils import CallTrace
from cqlparser import parseString
from meresco.core import Observable
from meresco.components.cqlsuggester import CqlSuggester
from meresco.components.ngram import LevenshteinSuggester
from weightless.core import compose, be

class MockNGramQuery(object):
    def __init__(self, results):
        self._results = results
    def executeNGramQuery(self, query, maxResults, fieldname=None):
        raise StopIteration(self._results[:maxResults])
        yield

class Interceptor(Observable):
    def suggestionsFor(self, *args, **kwargs):
        result = yield self.any.suggestionsFor(*args, **kwargs)
        yield result

    def suggestForCql(self, *args, **kwargs):
        result = yield self.any.suggestForCql(*args, **kwargs)
        yield result

class CqlSuggesterTest(TestCase):
    def testTwoWords(self):
        suggester = CallTrace('suggester')
        dna = be((Observable(),
            (Interceptor(),
                (CqlSuggester(),
                    (suggester,)
                )
            )
        ))
        def suggestionsFor(term):
            raise StopIteration(['wordy'])
            yield
        suggester.suggestionsFor = suggestionsFor
        cqlquery = parseString('word0 and word1')
        result = compose(dna.any.suggestForCql(cqlAST=cqlquery))
        self.assertEquals(['wordy'], result.next())

    def testTwoWordsWithRealSuggester(self):
        ngramQuery = MockNGramQuery([u'wordy', u'wordx'])
        suggester = LevenshteinSuggester(samples=50, threshold=10, maxResults=5)
        dna = be((Observable(),
            (Interceptor(),
                (suggester,
                    (ngramQuery,),
                )
            )
        ))
        self.assertEquals([False, ['wordy', 'wordx']], compose(dna.any.suggestionsFor('wordz')).next())
        self.assertEquals([True, ['wordx']], compose(dna.any.suggestionsFor('wordy')).next())

    def testCqlSuggester(self):
        ngramQuery = MockNGramQuery([u'wordy', u'wordx'])
        suggester = LevenshteinSuggester(samples=50, threshold=10, maxResults=5)
        dna = be((Observable(),
            (Interceptor(),
                (CqlSuggester(),
                    (suggester,
                        (ngramQuery,),
                    )
                )
            )
        ))
        cqlAST = parseString('wordz and wordy')
        self.assertEquals('wordz', cqlAST.children[0].children[0].children[0].children[0].children[0].children[0])
        result = compose(dna.any.suggestForCql(cqlAST))
        self.assertEquals([False, ['wordy', 'wordx']], result.next())

