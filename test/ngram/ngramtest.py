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
from cq2utils import CQ2TestCase, CallTrace

from merescocore.framework import Observable, TransactionScope, ResourceManager, be
from merescocore.components import Xml2Fields
from merescocore.components.tokenizefieldlet import TokenizeFieldlet

from merescocomponents.facetindex import LuceneIndex, Fields2LuceneDocumentTx
from merescocomponents.ngram.ngram import ngrams
from merescocomponents.ngram.suggester import _Suggestion
from merescocomponents.ngram import NGramQuery, LevenshteinSuggester, RatioSuggester, NGramIndex

from Levenshtein import distance, ratio
from lxml.etree import parse
from StringIO import StringIO
from PyLucene import BooleanQuery, BooleanClause, IndexReader, IndexWriter, IndexSearcher, TermQuery, Term, Field, StandardAnalyzer, Document, MatchAllDocsQuery


PUCH_WORDS = ['capuche', 'capuches', 'Capuchin', 'capuchins', 'Mapuche', 'Pampuch', 'puchera', 'pucherite', 'capuched', 'capuchin', 'puchero', 'PUC', 'Kampuchea', 'kampuchea', 'Puchanahua', 'sepuchral', 'puca', 'puce', 'puces', 'Puck', 'puck', 'pucka', 'pucks', 'Pupuluca', 'Puccini', 'puccini', 'puccoon', 'puceron', 'Pucida', 'pucker', 'puckish', 'puckle', 'SPUCDL', 'Chuch', 'Punch', 'punch', 'cappuccino', 'capucine', 'catapuce', 'catepuce', 'depucel', 'leucopus', 'mucopus', 'praepuce', 'prepuce', 'prepuces', 'Puccinia', 'puccinoid', 'puccoons', 'pucelage', 'pucellas', 'pucelle', 'puckball', 'puckered', 'puckerel', 'puckerer', 'puckering', 'puckers', 'puckery', 'Puckett', 'puckfist', 'puckfoist', 'puckishly', 'pucklike', 'puckling', 'puckrel', 'pucksey', 'puckster', 'sapucaia', 'unpucker', 'Vespucci', 'vespucci', 'Chucho', 'aneuch', 'aucht', 'bauch', 'bouch', 'Bruch', 'Buch', 'Buchan', 'buch', 'cauch', 'Chuck', 'chuck', 'couch', 'Cuchan', 'duchan', 'duchy', 'Eucha', 'Fauch', 'fuchi', 'Fuchs', 'heuch', 'hucho', 'Jauch', 'kauch', 'leuch', 'louch', 'Lucho', 'Manouch', 'mouch', 'much', 'nauch', 'nonsuch', 'nouche', 'nucha', 'ouch', 'pouch', 'Rauch', 'ruche', 'sauch', 'snouch', 'such', 'teuch', 'touch', 'touch-', 'touche', 'touchy', 'tuchis', 'tuchit', 'Uchean', 'Uchee', 'Uchish', 'vouch', 'wauch']


class NGramTest(CQ2TestCase):
    def setUp(self):
        class IntoTheFields(Observable):
            def addValues(self, values):
                for field, word in values:
                    self.do.addField(field, word)
        class NoOpSuggester(_Suggestion):
            def __init__(self):
                super(NoOpSuggester, self).__init__(25, 0, 25)
            def suggestionsFor(self, word, fieldname=None):
                return self._suggestionsFor(word, lambda term: 1, fieldname=fieldname)
        CQ2TestCase.setUp(self)
        index = LuceneIndex(self.tempdir, transactionName='batch')
        self.indexingDna = be((Observable(),
            (TransactionScope('batch'),
                (IntoTheFields(),
                    (TransactionScope('record'),
                        (NGramIndex(transactionName='record', fieldnames=['field0', 'field1']),
                            (index,)
                        )
                    )
                )
            )
        ))
        suggesterDna = be((Observable(),
            (NoOpSuggester(),
                (NGramQuery(2, fieldnames=['field0', 'field1']),
                    (index,)
                )
            )
        ))
        self.suggestionsFor = lambda word, fieldname=None: suggesterDna.any.suggestionsFor(word, fieldname=fieldname)

        self.addWord = lambda word, fieldname='field': self.indexingDna.do.addValues([(fieldname, word)])
    
        

    def testOneWord(self):
        self.addWord('appelboom')

        self.assertEquals((False, ['appelboom']), self.suggestionsFor('appel'))

    def testCreateIndexWithFunkyCharacters(self):
        self.addWord('Škvarla')
        self.addWord('Mockovčiaková')
        self.addWord('Jiří')
        self.addWord('ideeën')
        self.assertEquals((False, ['škvarla']), self.suggestionsFor('ar'))
        self.assertEquals((False, ['ideeën']), self.suggestionsFor('ee'))

        

    def testNgram(self):
        self.assertEquals(set(['bo', 'oo', 'om', 'boo', 'oom', 'boom']), set(ngrams('boom', N=4)))
        self.assertEquals(set(['bo', 'oo', 'om']), set(ngrams('boom', N=2)))
        self.assertEquals(set([u'šk','kv','va','ar','rl','la']), set(ngrams('škvarla', N=2)))


    def testLevenshtein(self):
        self.assertSuggestions(['puca', 'puce', 'puck', 'punch', 'puces'], 'puch', LevenshteinSuggester(50, 3, 5), ngramQuerySamples=50)

    def testRatio(self):
        self.assertSuggestions(['punch', 'puca', 'puce', 'puck', 'capuche'], 'puch', RatioSuggester(50, 0.6, 5), ngramQuerySamples=50)

    def testThresholdRatio(self):
        self.assertSuggestions([], 'puch', RatioSuggester(50, 0.9, 5), ngramQuerySamples=50)
        self.assertSuggestions(['punch'], 'puch', RatioSuggester(50, 0.8, 5), ngramQuerySamples=50)
        self.assertSuggestions(['punch', 'puca', 'puce', 'puck', 'capuche'], 'puch', RatioSuggester(50, 0.7, 5), ngramQuerySamples=50)
        self.assertSuggestions(['punch', 'puca', 'puce', 'puck', 'capuche'], 'puch', RatioSuggester(50, 0.6, 5), ngramQuerySamples=50)
        self.assertSuggestions(['punch', 'puca', 'puce', 'puck', 'capuche'], 'puch', RatioSuggester(50, 0.5, 5), ngramQuerySamples=50)


    def testThresholdLevenshtein(self):
        self.assertSuggestions([], 'puch', LevenshteinSuggester(50, 0, 5), ngramQuerySamples=50)
        self.assertSuggestions(['puca', 'puce', 'puck', 'punch'], 'puch', LevenshteinSuggester(50, 1, 5), ngramQuerySamples=50)
        self.assertSuggestions(['puca', 'puce', 'puck', 'punch', 'puces'], 'puch', LevenshteinSuggester(50, 2, 5), ngramQuerySamples=50)
        self.assertSuggestions(['puca', 'puce', 'puck', 'punch', 'puces'], 'puch', LevenshteinSuggester(50, 3, 5), ngramQuerySamples=50)
        self.assertSuggestions(['puca', 'puce', 'puck', 'punch', 'puces', 'Puck', 'pucka'], 'puch', LevenshteinSuggester(50, 4, 7), ngramQuerySamples=50)

    def testDoNotSuggestSameWord(self):
        self.assertSuggestions(['Punch', 'puca', 'puce', 'puck'], 'punch', LevenshteinSuggester(50, 5, 4), ngramQuerySamples=50)
        self.assertSuggestions(['Punch', 'capuche', 'Mapuche', 'Pampuch'], 'punch', RatioSuggester(50, 0.5, 4), ngramQuerySamples=50)

    def testUseMostFrequentlyAppearingWord(self):
        self.fail('TODO: first make new reality work, then fix this test.')
        class NoOpSuggester(_Suggestion):
            def __init__(self):
                super(NoOpSuggester, self).__init__(50, 0, 50)
            def suggestionsFor(self, word):
                return self._suggestionsFor(word, lambda term: 1)

        words = ['apartamentos', 'apartments', 'appartments', 'apartment', 'appartamento', 'appartamenti', 'appartements']
        freqs = [     2,             1024,          16,           256,          4,             1,             64      ]
        index = LuceneIndex(self.tempdir, transactionName='ngram')
        dna = \
            (Observable(),
                (TransactionScope('ngram'),
                    (NGramFieldlet(2, 'ngrams'),
                        (index,),
                        (ResourceManager('ngram', lambda resourceManager: Fields2LuceneDocumentTx(resourceManager, untokenized=[])),
                            (index,)
                        )
                    )
                ),
                (NGramQuery(2, 'ngrams'),
                    (index,)
                )
            )
        ngramFieldlet = be(dna)
        for word, freq in zip(words, freqs):
            for i in range(freq):
                ngramFieldlet.do.addField('field0', word)
        self.assertEquals(7, index.docCount())
        ngq = NGramQuery(2, 'ngrams')
        ngq.addObserver(index)
        suggester = NoOpSuggester()
        suggester.addObserver(ngq)
        self.assertTrue(all('ap' in word for word in words))
        inclusive, suggs = suggester.suggestionsFor('ap')
        self.assertEquals(['apartments', 'apartment', 'appartements', 'appartments', 'appartamento', 'apartamentos', 'appartamenti'], suggs)

    def testNGramForSpecificField(self):
        for i in range(3):
            self.addWord('value%s' % i)
            self.addWord('field0value%s' % i, fieldname='field0')
        inclusive, suggestions = self.suggestionsFor('val', 'field0')
        self.assertEquals(set(['field0value0', 'field0value1', 'field0value2']), set(suggestions))
        

    def assertSuggestions(self, expected, term, suggester, ngramQuerySamples):
        ngramindex = CallTrace('ngramindex')
        def executeQuery(query, start, stop, *args):
            return (len(PUCH_WORDS), PUCH_WORDS[:stop])
        ngramindex.executeQuery = executeQuery
        ngramQuery = NGramQuery(2, samples=ngramQuerySamples)
        ngramQuery.addObserver(ngramindex)
        suggester.addObserver(ngramQuery)
        inclusive, results = suggester.suggestionsFor(term)
        self.assertEquals(expected, list(results))
