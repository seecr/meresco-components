
from cq2utils import CQ2TestCase, CallTrace

from merescocomponents.ngram import NGramQuery

class NGramQueryTest(CQ2TestCase):
    def testOne(self):
        observer = CallTrace('observer')
        q = NGramQuery(2)
        q.addObserver(observer)
        observer.returnValues['executeQuery'] = (120, ['word%s$' % d for d in range(50)] )

        suggestions = q.executeNGramQuery('word', 2)

        self.assertEquals(['word0', 'word1'], list(suggestions))

    def testNGramQuery(self):
        ngramindex = CallTrace('ngramindex', returnValues = {'executeQuery': (2, ['term0$', 'term1$'])})
        ngramQuery = NGramQuery(2)
        ngramQuery.addObserver(ngramindex)
        suggestions = ngramQuery.executeNGramQuery('term0', 1234)
        self.assertEquals(['term0', 'term1'], list(suggestions))
        self.assertEquals('+field:ngrams$ +(ngrams:te ngrams:er ngrams:rm ngrams:m0)', str(ngramindex.calledMethods[0].args[0]))
        ngramindex.returnValues['executeQuery'] = (2, ['term2', 'term9'])
        suggestions = ngramQuery.executeNGramQuery('term0',87655)
        self.assertEquals(['term2', 'term9'], list(suggestions))

    def testNgramQueryFieldname(self):
        ngramindex = CallTrace('ngramindex', returnValues = {'executeQuery': (2, ['term0$some_fieldname', 'term1$some_fieldname'])})
        ngramQuery = NGramQuery(2, fieldnames=['some_fieldname'])
        ngramQuery.addObserver(ngramindex)
        suggestions = ngramQuery.executeNGramQuery('term0',9876, fieldname='some_fieldname')
        self.assertEquals(['term0', 'term1'], list(suggestions))
        self.assertEquals('+field:ngrams$some_fieldname +(ngrams:te ngrams:er ngrams:rm ngrams:m0)', str(ngramindex.calledMethods[0].args[0]))

    def testWordCardinality(self):
        docsetlist = CallTrace('docsetlist')
        drilldown = CallTrace('drilldownAndIndex')
        ngramQuery = NGramQuery(2, samples=50, fieldForSorting='fieldForSorting')
        ngramQuery.addObserver(drilldown)
        drilldown.returnValues['docsetlist'] = docsetlist
        drilldown.returnValues['executeQuery'] = (100, ['term%s$' % i for i in range(50)])
        cardinalities = dict(('term%s' % i, 1) for i in range(100))
        cardinalities['term0'] = 10
        cardinalities['term10'] = 2
        cardinalities['term20'] = 20
        docsetlist.methods['cardinality'] = lambda term: cardinalities.get(term, 0)

        suggestions = ngramQuery.executeNGramQuery('term', maxResults=5)

        self.assertEquals(['term20', 'term0', 'term10', 'term1', 'term2'], list(suggestions))
        self.assertEquals(['cardinality']*50, [m.name for m in docsetlist.calledMethods])
        docsetlistmethods = [m for m in drilldown.calledMethods if m.name == 'docsetlist']
        self.assertTrue("docsetlist('fieldForSorting')" in [str(m) for m in docsetlistmethods])
        self.assertEquals(50, len(docsetlistmethods))
        othermethods = [m for m in drilldown.calledMethods if m.name != 'docsetlist']
        self.assertEquals(1, len(othermethods))
        self.assertEquals({'start': 0, 'stop': 50}, othermethods[0].kwargs)
        self.assertEquals(['+field:ngrams$ +(ngrams:te ngrams:er ngrams:rm)'], [str(a) for a in othermethods[0].args])
        
        
