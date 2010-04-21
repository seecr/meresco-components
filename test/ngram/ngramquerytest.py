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
        
        
