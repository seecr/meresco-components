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

from merescocore.framework import Observable, TransactionScope, ResourceManager, be, Transaction
from merescocore.components import Xml2Fields
from merescocore.components.tokenizefieldlet import TokenizeFieldlet

from merescocomponents.facetindex import LuceneIndex, Fields2LuceneDocumentTx, Document, Drilldown
from merescocomponents.ngram.ngram import ngrams
from merescocomponents.ngram.suggester import _Suggestion
from merescocomponents.ngram import NGramQuery, LevenshteinSuggester, RatioSuggester, NGramIndex

from Levenshtein import distance, ratio
from lxml.etree import parse
from StringIO import StringIO

from os.path import join

_PUCH_WORDS = ['capuche', 'capuches', 'Capuchin', 'capuchins', 'Mapuche', 'Pampuch', 'puchera', 'pucherite', 'capuched', 'capuchin', 'puchero', 'PUC', 'Kampuchea', 'kampuchea', 'Puchanahua', 'sepuchral', 'puca', 'puce', 'puces', 'Puck', 'puck', 'pucka', 'pucks', 'Pupuluca', 'Puccini', 'puccini', 'puccoon', 'puceron', 'Pucida', 'pucker', 'puckish', 'puckle', 'SPUCDL', 'Chuch', 'Punch', 'punch', 'cappuccino', 'capucine', 'catapuce', 'catepuce', 'depucel', 'leucopus', 'mucopus', 'praepuce', 'prepuce', 'prepuces', 'Puccinia', 'puccinoid', 'puccoons', 'pucelage', 'pucellas', 'pucelle', 'puckball', 'puckered', 'puckerel', 'puckerer', 'puckering', 'puckers', 'puckery', 'Puckett', 'puckfist', 'puckfoist', 'puckishly', 'pucklike', 'puckling', 'puckrel', 'pucksey', 'puckster', 'sapucaia', 'unpucker', 'Vespucci', 'vespucci', 'Chucho', 'aneuch', 'aucht', 'bauch', 'bouch', 'Bruch', 'Buch', 'Buchan', 'buch', 'cauch', 'Chuck', 'chuck', 'couch', 'Cuchan', 'duchan', 'duchy', 'Eucha', 'Fauch', 'fuchi', 'Fuchs', 'heuch', 'hucho', 'Jauch', 'kauch', 'leuch', 'louch', 'Lucho', 'Manouch', 'mouch', 'much', 'nauch', 'nonsuch', 'nouche', 'nucha', 'ouch', 'pouch', 'Rauch', 'ruche', 'sauch', 'snouch', 'such', 'teuch', 'touch', 'touch-', 'touche', 'touchy', 'tuchis', 'tuchit', 'Uchean', 'Uchee', 'Uchish', 'vouch', 'wauch']

PUCH_WORDS = [unicode(word) for word in _PUCH_WORDS]

class NGramTest(CQ2TestCase):
    def setUp(self):
        global identifierNr
        identifierNr = 0
        class DictToFields(Observable):
            def addDict(self, aDictionary):
                self.ctx.tx.locals['id'] = aDictionary['identifier']
                for k,v in aDictionary.items():
                    self.do.addField(k, v)
        class NoOpSuggester(_Suggestion):
            def __init__(self):
                super(NoOpSuggester, self).__init__(25, 0, 25)
            def sortKey(*args):
                return 1
            def threshold(*args):
                return True
        CQ2TestCase.setUp(self)
        ngramIndex = LuceneIndex(join(self.tempdir,'ngrams'), transactionName='batch')
        documentIndex = LuceneIndex(join(self.tempdir, 'document'), transactionName='batch')
        allfieldsDrilldown = Drilldown(['allfields'], transactionName='batch')
        self.indexingDna = be((Observable(),
            (TransactionScope('batch'),
                (TransactionScope('record'),
                    (DictToFields(),
                        (NGramIndex(transactionName='record', fieldnames=['field0', 'field1']),
                            (ngramIndex,)
                        ),
                        (ResourceManager('record', lambda resourceManager: Fields2LuceneDocumentTx(resourceManager, untokenized=[])),
                            (documentIndex,
                                (allfieldsDrilldown,)
                            )
                        )
                    )
                )
            )
        ))
        suggesterDna = be((Observable(),
            (NoOpSuggester(),
                (NGramQuery(2, samples=50, fieldnames=['field0', 'field1'], fieldForSorting='allfields'),
                    (ngramIndex,),
                    (allfieldsDrilldown,)
                )
            )
        ))
        self.suggestionsFor = lambda word, fieldname=None: suggesterDna.any.suggestionsFor(word, fieldname=fieldname)

        def addWord(word, fieldname='field'):
            global identifierNr
            identifierNr += 1
            document = {
                'identifier': 'id%s'%identifierNr,
                'allfields': word
            }
            document[fieldname] = word
            self.indexingDna.do.addDict(document)

        self.addWord = addWord
    
        

    def testOneWord(self):
        self.addWord('appelboom')
        self.assertEquals((False, ['appelboom']), self.suggestionsFor('appel'))

    def testCreateIndexWithFunkyCharacters(self):
        self.addWord('Škvarla')
        self.addWord('Mockovčiaková')
        self.addWord('Jiří')
        self.addWord('ideeën')
        self.assertEquals((False, ['škvarla']), self.suggestionsFor('ar'))
        self.assertEquals(str, type(self.suggestionsFor('ar')[1][0]))
        self.assertEquals((False, ['ideeën']), self.suggestionsFor('ee'))
        self.assertEquals((False, ['škvarla']), self.suggestionsFor('Škvarla'))
        

    def testNgram(self):
        self.assertEquals(set(['bo', 'oo', 'om', 'boo', 'oom', 'boom']), set(ngrams('boom', N=4)))
        self.assertEquals(set(['bo', 'oo', 'om']), set(ngrams('boom', N=2)))
        self.assertEquals(set([u'šk','kv','va','ar','rl','la']), set(ngrams(u'škvarla', N=2)))


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
        puch_words_with_c = [p for p in PUCH_WORDS if p.lower().startswith('c')]
        for word in PUCH_WORDS:
            self.addWord(word)
        for word in puch_words_with_c:
            self.addWord(word)
            self.addWord(word)

        inclusive, suggestions = self.suggestionsFor('puch')
        firstletters = ''.join(word[0] for word in suggestions)
        self.assertEquals('ccccc', firstletters[:5])
        self.assertFalse('c' in firstletters[5:], firstletters)

    def testUseMostFrequentlyAppearingWordForFields(self):
        puch_words_with_p = [p for p in PUCH_WORDS if p.lower().startswith('p')]
        puch_words_with_p_without_puc = [p for p in PUCH_WORDS if p.lower().startswith('p') and not p.lower().startswith('puc')]
        for word in puch_words_with_p:
            self.addWord(word)
            self.addWord(word, 'field0')
        for word in puch_words_with_p_without_puc:
            self.addWord(word)
            self.addWord(word, 'field0')
        inclusive, suggestions = self.suggestionsFor('puch', fieldname='field0')
        threeletterwords = [word[:3] for word in suggestions]
        self.assertTrue('puc' not in threeletterwords[:5])
        self.assertEquals(['puc']*20, threeletterwords[5:])


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
