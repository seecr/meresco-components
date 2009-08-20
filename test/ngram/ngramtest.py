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
from merescocomponents.ngram.ngram import ngrams, _Suggestion
from merescocomponents.ngram import NGramFieldlet, NGramQuery, LevenshteinSuggester, RatioSuggester, NGramIndex

from Levenshtein import distance, ratio
from lxml.etree import parse
from StringIO import StringIO
from PyLucene import BooleanQuery, BooleanClause, IndexReader, IndexWriter, IndexSearcher, TermQuery, Term, Field, StandardAnalyzer, Document, MatchAllDocsQuery


PUCH_WORDS = ['capuche', 'capuches', 'Capuchin', 'capuchins', 'Mapuche', 'Pampuch', 'puchera', 'pucherite', 'capuched', 'capuchin', 'puchero', 'PUC', 'Kampuchea', 'kampuchea', 'Puchanahua', 'sepuchral', 'puca', 'puce', 'puces', 'Puck', 'puck', 'pucka', 'pucks', 'Pupuluca', 'Puccini', 'puccini', 'puccoon', 'puceron', 'Pucida', 'pucker', 'puckish', 'puckle', 'SPUCDL', 'Chuch', 'Punch', 'punch', 'cappuccino', 'capucine', 'catapuce', 'catepuce', 'depucel', 'leucopus', 'mucopus', 'praepuce', 'prepuce', 'prepuces', 'Puccinia', 'puccinoid', 'puccoons', 'pucelage', 'pucellas', 'pucelle', 'puckball', 'puckered', 'puckerel', 'puckerer', 'puckering', 'puckers', 'puckery', 'Puckett', 'puckfist', 'puckfoist', 'puckishly', 'pucklike', 'puckling', 'puckrel', 'pucksey', 'puckster', 'sapucaia', 'unpucker', 'Vespucci', 'vespucci', 'Chucho', 'aneuch', 'aucht', 'bauch', 'bouch', 'Bruch', 'Buch', 'Buchan', 'buch', 'cauch', 'Chuck', 'chuck', 'couch', 'Cuchan', 'duchan', 'duchy', 'Eucha', 'Fauch', 'fuchi', 'Fuchs', 'heuch', 'hucho', 'Jauch', 'kauch', 'leuch', 'louch', 'Lucho', 'Manouch', 'mouch', 'much', 'nauch', 'nonsuch', 'nouche', 'nucha', 'ouch', 'pouch', 'Rauch', 'ruche', 'sauch', 'snouch', 'such', 'teuch', 'touch', 'touch-', 'touche', 'touchy', 'tuchis', 'tuchit', 'Uchean', 'Uchee', 'Uchish', 'vouch', 'wauch']

def createNGramHelix(observert):
    return be(
        (Observable(),
            (TransactionScope('ngram'),
                (NGramFieldlet(2, 'ngrams'),
                    (observert,)
                )
            )
        )
    )

class NGramTest(CQ2TestCase):
    def testDNA(self):
        def ngramQuery(word, N=2):
            query = BooleanQuery()
            for ngram in ngrams(word, N):
                query.add(BooleanClause(TermQuery(Term('ngrams', ngram)), BooleanClause.Occur.SHOULD))
            return query

        index = LuceneIndex(self.tempdir)
        dna = \
            (Observable(),
                (TransactionScope('ngram'),
                    (Xml2Fields(),
                        (NGramFieldlet(2, 'ngrams'),
                            (index,),
                            (ResourceManager('ngram', lambda resourceManager: Fields2LuceneDocumentTx(resourceManager, untokenized=[])),
                                (index,)
                            )
                        )
                    )
                ),
                (NGramQuery(2, 'ngrams'),
                    (index,)
                )
            )
        x = be(dna)
        xmlNode = parse(StringIO(u'<node><subnode>ideeën</subnode></node>'))
        x.do.addXml(xmlNode)
        index.commit()
        index.start()
        total, hits = index.executeQuery(ngramQuery(u'ideeën'))
        self.assertEquals(1, index.docCount())
        self.assertEquals('ideeën', hits[0])

    def testCreateIndex(self):
        def addWord(index, word):
            d = Document()
            d.add(Field('term', word, Field.Store.YES, Field.Index.TOKENIZED))
            d.add(Field('ngrams', ' '.join(ngrams(word)), Field.Store.NO, Field.Index.TOKENIZED))
            index.addDocument(d)
        index = IndexWriter(self.tempdir, StandardAnalyzer(), True)
        addWord(index, 'appelboom')
        index.flush()
        searcher = IndexSearcher(self.tempdir)
        hits = searcher.search(TermQuery(Term('ngrams', 'ap')))
        self.assertEquals('appelboom', hits[0].get('term'))

    def testCreateIndexWithFunkyCharacters(self):
        def addWord(index, word):
            d = Document()
            d.add(Field('term', word, Field.Store.YES, Field.Index.TOKENIZED))
            d.add(Field('ngrams', ' '.join(ngrams(word)), Field.Store.NO, Field.Index.TOKENIZED))
            index.addDocument(d)
        index = IndexWriter(self.tempdir, StandardAnalyzer(), True)
        addWord(index,'Škvarla')
        addWord(index,'Mockovčiaková')
        addWord(index,'Jiří')
        index.flush()
        searcher = IndexSearcher(self.tempdir)
        hits = searcher.search(TermQuery(Term('ngrams', 'ar')))
        self.assertEquals('Škvarla', hits[0].get('term'))


    def testNgram(self):
        self.assertEquals(set(['bo', 'oo', 'om', 'boo', 'oom', 'boom']), set(ngrams('boom', N=4)))
        self.assertEquals(set(['bo', 'oo', 'om']), set(ngrams('boom', N=2)))

    def testNGramFieldLet(self):
        observert = CallTrace('Observert', returnValues={'executeQueryWithField': (0, [])})
        ngramFieldlet = createNGramHelix(observert)
        ngramFieldlet.do.addField('field0', 'term0')
        self.assertEquals(5, len(observert.calledMethods))
        self.assertEquals("begin()", str(observert.calledMethods[0]))
        self.assertEquals('changeBoost', observert.calledMethods[2].name)
        self.assertEquals('addField', observert.calledMethods[3].name)
        self.assertEquals(('ngrams', 'te er rm m0'), observert.calledMethods[3].args)

    def testNGramFieldLetQueriesForWord(self):
        observert = CallTrace('Observert', returnValues={'executeQueryWithField': (1, ['1'])})
        ngramFieldlet = createNGramHelix(observert)
        ngramFieldlet.do.addField('field0', 'term0')
        self.assertEquals("[begin(), executeQueryWithField(<class __id__>, 'appears'), "
            "changeBoost(0.069314718056), addField('ngrams', 'te er rm m0'), "
            "addField(value='2', store=<class True>, name='appears')]",
            str(observert.calledMethods))

    def testWordisIDinTransactionScope(self):
        txlocals = {}
        class Observert(Observable):
            def addField(self, *args, **kwargs):
                txlocals.update(self.ctx.tx.locals)
            def executeQueryWithField(*args, **kwargs):
                return 0, []
            def changeBoost(*args):
                pass
        x = createNGramHelix(Observert())
        x.do.addField('field0', 'term0')
        self.assertEquals({'id': u'term0'}, txlocals)

    def testNgramQuery(self):
        ngramindex = CallTrace('ngramindex', returnValues = {'executeQuery': (2, ['term0', 'term1'])})
        ngramQuery = NGramQuery(2, 'ngrams')
        ngramQuery.addObserver(ngramindex)
        total, hits = ngramQuery.executeNGramQuery('term0', 1234)
        self.assertEquals(['term0', 'term1'], list(hits))
        self.assertEquals('ngrams:te ngrams:er ngrams:rm ngrams:m0', str(ngramindex.calledMethods[0].args[0]))
        ngramindex.returnValues['executeQuery'] = (2, ['term2', 'term9'])
        total, hits = ngramQuery.executeNGramQuery('term0',87655)
        self.assertEquals(['term2', 'term9'], list(hits))

    def testNgramQueryFieldname(self):
        ngramindex = CallTrace('ngramindex', returnValues = {'executeQuery': (2, ['term0', 'term1'])})
        ngramQuery = NGramQuery(2, 'some_fieldname')
        ngramQuery.addObserver(ngramindex)
        total, hits = ngramQuery.executeNGramQuery('term0',9876)
        self.assertEquals(['term0', 'term1'], list(hits))
        self.assertEquals('some_fieldname:te some_fieldname:er some_fieldname:rm some_fieldname:m0', str(ngramindex.calledMethods[0].args[0]))
        ngramindex.returnValues['executeQuery'] = (2,['term2', 'term9'])

    def testLevenshtein(self):
        self.assertSuggestions(['puca', 'puce', 'puck', 'punch', 'puces'], 'puch', LevenshteinSuggester(50, 3, 5))

    def testRatio(self):
        self.assertSuggestions(['punch', 'puca', 'puce', 'puck', 'capuche'], 'puch', RatioSuggester(50, 0.6, 5))

    def testThresholdRatio(self):
        self.assertSuggestions([], 'puch', RatioSuggester(50, 0.9, 5))
        self.assertSuggestions(['punch'], 'puch', RatioSuggester(50, 0.8, 5))
        self.assertSuggestions(['punch', 'puca', 'puce', 'puck', 'capuche'], 'puch', RatioSuggester(50, 0.7, 5))
        self.assertSuggestions(['punch', 'puca', 'puce', 'puck', 'capuche'], 'puch', RatioSuggester(50, 0.6, 5))
        self.assertSuggestions(['punch', 'puca', 'puce', 'puck', 'capuche'], 'puch', RatioSuggester(50, 0.5, 5))


    def testThresholdLevenshtein(self):
        self.assertSuggestions([], 'puch', LevenshteinSuggester(50, 0, 5))
        self.assertSuggestions(['puca', 'puce', 'puck', 'punch'], 'puch', LevenshteinSuggester(50, 1, 5))
        self.assertSuggestions(['puca', 'puce', 'puck', 'punch', 'puces'], 'puch', LevenshteinSuggester(50, 2, 5))
        self.assertSuggestions(['puca', 'puce', 'puck', 'punch', 'puces'], 'puch', LevenshteinSuggester(50, 3, 5))
        self.assertSuggestions(['puca', 'puce', 'puck', 'punch', 'puces', 'Puck', 'pucka'], 'puch', LevenshteinSuggester(50, 4, 7))

    def testDoNotSuggestSameWord(self):
        self.assertSuggestions(['Punch', 'puca', 'puce', 'puck'], 'punch', LevenshteinSuggester(50, 5, 4))
        self.assertSuggestions(['Punch', 'capuche', 'Mapuche', 'Pampuch'], 'punch', RatioSuggester(50, 0.5, 4))

    def testUseMostFrequentlyAppearingWord(self):
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
        class NoOpSuggester(_Suggestion):
            def __init__(self):
                super(NoOpSuggester, self).__init__(50, 0, 50)
            def suggestionsFor(self, word, fieldname=None):
                return self._suggestionsFor(word, lambda term: 1, fieldname=fieldname)

        index = LuceneIndex(self.tempdir, transactionName='ngram')
        ngramFieldlet = be( \
            (Observable(),
                (TransactionScope('ngram'),
                    (NGramFieldlet(2, 'ngrams', fieldNames=['field0', 'field1']),
                        (index,),
                        (ResourceManager('ngram', lambda resourceManager: Fields2LuceneDocumentTx(resourceManager, untokenized=[])),
                            (index,)
                        )
                    )
                ),
            )
        )

        for field, word in [('field0', 'apparaat'), ('field1', 'parade')]:
            for i in range(10):
                ngramFieldlet.do.addField(field, word)
        self.assertEquals(2, index.docCount())


        ngq = NGramQuery(2, 'ngrams', fieldNames=['field0', 'field1'])
        ngq.addObserver(index)
        suggester = NoOpSuggester()
        suggester.addObserver(ngq)
        inclusive, suggs = suggester.suggestionsFor('ar')
        self.assertEquals([u'parade', u'apparaat'], suggs)
        inclusive, suggs = suggester.suggestionsFor('ar', fieldname='field0')
        self.assertEquals([u'apparaat'], suggs)

    def testBadgerBadgerBadger(self):
        class NoOpSuggester(_Suggestion):
            def __init__(self):
                super(NoOpSuggester, self).__init__(50, 0, 50)
            def suggestionsFor(self, word, fieldname=None):
                return self._suggestionsFor(word, lambda term: 1, fieldname=fieldname)

        index = LuceneIndex(self.tempdir, transactionName='batch')
        class IntoTheFields(Observable):
            def addValueList(self, values):
                #print 'ValueList'
                for field, word in values:
                    #if 'pipeline' in word:
                        self.do.addField(field, word)
                #print 'AAP', '\n'.join(str(c) for c in index._commandQueue)

        dna = be((Observable(),
            (TransactionScope('batch'),
                (IntoTheFields(),
                    (NGramIndex(['field0', 'field1']),
                        (index,),
                    )
                )
            )
        ))


        values = [
            [('field0', 'pipeline'),
            ],
            [('field0', 'pipeline'),
            ('field1', 'pipeline'),
            ],
        ]
        for i, valuelist in enumerate(values):
            dna.do.addValueList(valuelist)
        from merescocomponents.facetindex.tools.listIndexedFields import listTerms

        termDocs = index._reader.termDocs()
        termEnum = index._reader.terms(Term('__id__', ''))
        termCount = {}
        while True:
            if termEnum.term().field() != '__id__':
                break
            termDocs.seek(termEnum)
            docIds = []
            while termDocs.next():
                docIds.append(termDocs.doc())
            termCount[termEnum.term().text()] = len(docIds)
            if not termEnum.next():
                break

        self.assertEquals([], [(term,count) for term, count in termCount.items() if count >= 2])



        #ngq = NGramQuery(2, 'ngrams', fieldNames=['field0'])
        #ngq.addObserver(index)
        #suggester = NoOpSuggester()
        #suggester.addObserver(ngq)
        #inclusive, suggs = suggester.suggestionsFor('ar')
        #self.assertEquals([u'parade', u'apparaat'], suggs)
        #inclusive, suggs = suggester.suggestionsFor('ar', fieldname='field0')
        #self.assertEquals([u'apparaat'], suggs)



    def testNoAppearsPresent(self):
        observert = CallTrace('Observert', returnValues={'executeQueryWithField': (1, [None])})
        ngramFieldlet = createNGramHelix(observert)
        ngramFieldlet.do.addField('field0', 'term0')

    def assertSuggestions(self, expected, term, suggester):
        ngramindex = CallTrace('ngramindex')
        def executeQuery(query, start, stop, *args):
            return (len(PUCH_WORDS), PUCH_WORDS[:stop])
        ngramindex.executeQuery = executeQuery
        ngramQuery = NGramQuery(2, 'ngrams')
        ngramQuery.addObserver(ngramindex)
        suggester.addObserver(ngramQuery)
        inclusive, results = suggester.suggestionsFor(term)
        self.assertEquals(expected, list(results))




    def XXXXXXXXtestIntegrationWords(self):
        def addWord(index, word):
            d = Document()
            d.add(Field('term', word, Field.Store.YES, Field.Index.TOKENIZED))
            d.add(Field('ngrams', ' '.join(ngrams(word)), Field.Store.NO, Field.Index.TOKENIZED))
            index.addDocument(d)
        index = IndexWriter('index', StandardAnalyzer(), True)
        f = open('/usr/share/dict/words')
        for word in f:
            #print word
            addWord(index, word.strip().decode('iso 8859-1'))
        index.flush()
        index.close()

        searcher = IndexSearcher('index')

        def ngramQuery(word, N=2):
            query = BooleanQuery()
            for ngram in ngrams(word, N):
                query.add(BooleanClause(TermQuery(Term('ngrams', ngram)), BooleanClause.Occur.SHOULD))
            return query

        for word in ['Alabama', 'alhambra', 'albuqurqi', 'matematics', 'restauration', 'abridgement', 'entousiast', 'puch', 'grnt', 'carot', 'from', 'sema', 'bord', 'enrgie', 'energie', 'enery', 'energy' ]:
            print "'%s', did you mean:" % word
            for N in range(2,4):
                hits = iter(searcher.search(ngramQuery(word, N=N)))
                suggestions = []
                for n in range(50): #seems roughly good in this test for 'grnt'
                    hit = hits.next()
                    score = hit.getScore()
                    term = hit.get('term')
                    suggestions.append((term, score, distance(unicode(term), unicode(word)), ratio(unicode(term), unicode(word))))
                if word == 'puch':
                    print [x[0] for x in suggestions]
                levenSuggs = sorted(suggestions, key=lambda x: x[2])[:5]
                ratioSuggs = sorted(suggestions, key=lambda x: x[3], reverse=True)[:5]
                print '    Score:', ', '.join('%s (%.1f)' % (sugg[0], sugg[1]) for sugg in suggestions[:5])
                print '    Leven (n=%d):'%N, ', '.join('%s (%.1f)' % (sugg[0], sugg[2]) for sugg in levenSuggs if sugg[2] < 5)
                print '    Ratio (n=%d):'%N, ', '.join('%s (%.1f)' % (sugg[0], sugg[3]) for sugg in ratioSuggs if sugg[3] > 0.65)

    def XXXXtestIntegrationLiveWords(self):
        def addWord(index, word):
            d = Document()
            d.add(Field('term', word, Field.Store.YES, Field.Index.TOKENIZED))
            d.add(Field('ngrams', ' '.join(ngrams(word)), Field.Store.NO, Field.Index.TOKENIZED))
            index.addDocument(d)
        index = IndexWriter('index2', StandardAnalyzer(), True)
        f = open('/home/meresco/words.txt')
        for word in f:
            #print word
            addWord(index, word.strip().decode('iso 8859-1'))
        index.flush()
        index.close()

        searcher = IndexSearcher('index2')

        def ngramQuery(word, N=2):
            query = BooleanQuery()
            for ngram in ngrams(word, N):
                query.add(BooleanClause(TermQuery(Term('ngrams', ngram)), BooleanClause.Occur.SHOULD))
            return query

        for word in ['Nederland', 'Rafael', 'config', 'susceptibility' ]:
            print "'%s', did you mean:" % word
            for N in range(2,4):
                hits = iter(searcher.search(ngramQuery(word, N=N)))
                suggestions = []
                for n in range(50): #seems roughly good in this test for 'grnt'
                    hit = hits.next()
                    score = hit.getScore()
                    term = hit.get('term')
                    suggestions.append((term, score, distance(unicode(term), unicode(word)), ratio(unicode(term), unicode(word))))
                if word == 'puch':
                    print [x[0] for x in suggestions]
                levenSuggs = sorted(suggestions, key=lambda x: x[2])[:5]
                ratioSuggs = sorted(suggestions, key=lambda x: x[3], reverse=True)[:5]
                print '    Score:', ', '.join('%s (%.1f)' % (sugg[0], sugg[1]) for sugg in suggestions[:5])
                print '    Leven (n=%d):'%N, ', '.join('%s (%.1f)' % (sugg[0], sugg[2]) for sugg in levenSuggs if sugg[2] < 5)
                print '    Ratio (n=%d):'%N, ', '.join('%s (%.1f)' % (sugg[0], sugg[3]) for sugg in ratioSuggs if sugg[3] > 0.65)
