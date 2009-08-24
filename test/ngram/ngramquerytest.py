
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
