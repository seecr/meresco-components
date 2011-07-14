## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2008 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2008 Tilburg University http://www.uvt.nl
#    Copyright (C) 2008-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2009-2010 Seek You Too (CQ2) http://www.cq2.nl
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

from meresco.core import be, Observable
from meresco.components.ngram import NGramQuery
from meresco.components.facetindex import Response
from weightless.core import compose

class Interceptor(Observable):
    def executeNGramQuery(self, *args, **kwargs):
        result = yield self.asyncany.executeNGramQuery(*args, **kwargs)
        yield result

class NGramQueryTest(CQ2TestCase):
    def testOne(self):
        observer = CallTrace('observer')
        ngramQuery = NGramQuery(2)
        dna = be((Observable(),
            (Interceptor(),
                (ngramQuery,
                    (observer,)
                )
            )
        ))
        response = Response(total=120, hits=['word%s$' % d for d in range(50)])
        observer.exceptions['executeQuery'] = StopIteration(response)

        composedGenerator = compose(dna.any.executeNGramQuery('word', 2))
        suggestions = composedGenerator.next()

        self.assertEquals(['word0', 'word1'], list(suggestions))

    def testNGramQuery(self):
        ngramindex = CallTrace('ngramindex')
        response = Response(total=2, hits=['term0$', 'term1$'])
        ngramindex.exceptions['executeQuery'] = StopIteration(response)
        ngramQuery = NGramQuery(2)
        dna = be((Observable(),
            (Interceptor(),
                (ngramQuery,
                    (ngramindex,)
                )
            )
        ))
        composedGenerator = compose(dna.any.executeNGramQuery('term0', 1234))
        suggestions = composedGenerator.next()
        self.assertEquals(['term0', 'term1'], list(suggestions))
        self.assertEquals('+field:ngrams$ +(ngrams:te ngrams:er ngrams:rm ngrams:m0)', str(ngramindex.calledMethods[0].args[0]))
        response = Response(total=2, hits=['term2', 'term9'])
        ngramindex.exceptions['executeQuery'] = StopIteration(response)
        suggestions = compose(dna.any.executeNGramQuery('term0',87655)).next()
        self.assertEquals(['term2', 'term9'], list(suggestions))

    def testNgramQueryFieldname(self):
        ngramindex = CallTrace('ngramindex')
        response = Response(total=2, hits=['term0$some_fieldname', 'term1$some_fieldname'])
        ngramindex.exceptions['executeQuery'] = StopIteration(response)
        ngramQuery = NGramQuery(2, fieldnames=['some_fieldname'])
        dna = be((Observable(),
            (Interceptor(),
                (ngramQuery,
                    (ngramindex,)
                )
            )
        ))
        suggestions = compose(dna.any.executeNGramQuery('term0',9876, fieldname='some_fieldname')).next()
        self.assertEquals(['term0', 'term1'], list(suggestions))
        self.assertEquals('+field:ngrams$some_fieldname +(ngrams:te ngrams:er ngrams:rm ngrams:m0)', str(ngramindex.calledMethods[0].args[0]))

    def testWordCardinality(self):
        docsetlist = CallTrace('docsetlist')
        drilldown = CallTrace('drilldownAndIndex')
        ngramQuery = NGramQuery(2, samples=50, fieldForSorting='fieldForSorting')
        dna = be((Observable(),
            (Interceptor(),
                (ngramQuery,
                    (drilldown,)
                )
            )
        ))
        drilldown.returnValues['docsetlist'] = docsetlist
        response = Response(total=100, hits=['term%s$' % i for i in range(50)])
        drilldown.exceptions['executeQuery'] = StopIteration(response)
        cardinalities = dict(('term%s' % i, 1) for i in range(100))
        cardinalities['term0'] = 10
        cardinalities['term10'] = 2
        cardinalities['term20'] = 20
        docsetlist.methods['cardinality'] = lambda term: cardinalities.get(term, 0)

        suggestions = compose(dna.any.executeNGramQuery('term', maxResults=5)).next()

        self.assertEquals(['term20', 'term0', 'term10', 'term1', 'term2'], list(suggestions))
        self.assertEquals(['cardinality']*50, [m.name for m in docsetlist.calledMethods])
        docsetlistmethods = [m for m in drilldown.calledMethods if m.name == 'docsetlist']
        self.assertTrue("docsetlist('fieldForSorting')" in [str(m) for m in docsetlistmethods])
        self.assertEquals(50, len(docsetlistmethods))
        othermethods = [m for m in drilldown.calledMethods if m.name != 'docsetlist']
        self.assertEquals(1, len(othermethods))
        self.assertEquals({'start': 0, 'stop': 50}, othermethods[0].kwargs)
        self.assertEquals(['+field:ngrams$ +(ngrams:te ngrams:er ngrams:rm)'], [str(a) for a in othermethods[0].args])
        
        
