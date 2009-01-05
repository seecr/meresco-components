## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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
from PyLucene import Term, TermQuery, IndexReader, MatchAllDocsQuery

from cq2utils import CQ2TestCase, CallTrace

from merescocomponents.facetindex.document import Document
from merescocomponents.facetindex.drilldown import Drilldown
from merescocomponents.facetindex.drilldownfieldnames import DrilldownFieldnames
from merescocomponents.facetindex.lucene import LuceneIndex

from merescocomponents.facetindex.docset import DocSet
from merescocomponents.facetindex.docsetlist import DocSetList

class DrilldownTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.index = LuceneIndex(self.tempdir, timer=TimerForTestSupport())

    def tearDown(self):
        self.index.close()
        CQ2TestCase.tearDown(self)

    #Helper functions:
    def addUntokenized(self, documents):
        for docId, fields in documents:
            myDocument = Document(docId)
            for field, value in fields.items():
                myDocument.addIndexedField(field, value, tokenize = False)
            self.index.addDocument(myDocument)

    def testIndexStarted(self):
        self.addUntokenized([('id', {'field_0': 'this is term_0'})])
        drilldown = Drilldown(['field_0'])
        reader = IndexReader.open(self.tempdir)
        drilldown.indexStarted(reader)
        field, results = drilldown.drilldown(DocSet('query', data=[0]), [('field_0', 10, False)]).next()
        self.assertEquals('field_0', field)
        self.assertEquals([('this is term_0', 1)], list(results))

    def testDrilldown(self):
        self.addUntokenized([
            ('0', {'field_0': 'this is term_0', 'field_1': 'inquery'}),
            ('1', {'field_0': 'this is term_1', 'field_1': 'inquery'}),
            ('2', {'field_0': 'this is term_1', 'field_1': 'inquery'}),
            ('3', {'field_0': 'this is term_2', 'field_1': 'cannotbefound'})])
        self.index._writer.flush()
        reader = IndexReader.open(self.tempdir)
        #convertor = LuceneRawDocSets(reader, ['field_0', 'field_1'])
        drilldown = Drilldown(['field_0', 'field_1'])
        drilldown.indexStarted(reader)
        query = TermQuery(Term("field_1", "inquery"))
        total, queryResults = self.index.executeQuery(query)
        self.assertEquals(3, total)
        self.assertEquals(['0', '1', '2'], queryResults)
        queryDocset = self.index.docsetFromQuery(query)
        drilldownResult = list(drilldown.drilldown(queryDocset, [('field_0', 0, False), ('field_1', 0, False)]))
        self.assertEquals(2, len(drilldownResult))
        result = dict(drilldownResult)
        self.assertEquals(['field_0', 'field_1'], result.keys())
        self.assertEquals(set([("this is term_0", 1), ("this is term_1", 2)]), set(result['field_0']))
        self.assertEquals([("inquery", 3)], list(result['field_1']))

    def testSortingOnCardinality(self):
        self.addUntokenized([
            ('0', {'field0': 'term1'}),
            ('1', {'field0': 'term1'}),
            ('2', {'field0': 'term2'}),
            ('3', {'field0': 'term0'})])
        reader = IndexReader.open(self.tempdir)
        drilldown = Drilldown(['field0'])
        drilldown.indexStarted(reader)
        hits = self.index.docsetFromQuery(MatchAllDocsQuery())
        ddData = list(drilldown.drilldown(hits, [('field0', 0, False)]))
        self.assertEquals([('term0',1), ('term1',2), ('term2',1)], list(ddData[0][1]))
        result = list(drilldown.drilldown(hits, [('field0', 0, True)]))
        self.assertEquals([('term1',2), ('term0',1), ('term2',1)], list(result[0][1]))


    def testAppendToRow(self):
        docsetlist = DocSetList([])
        docsetlist.addDocument(0, ['term0', 'term1'])
        self.assertEquals('term0', docsetlist[0].term())
        self.assertEquals('term1', docsetlist[1].term())
        self.assertEquals([('term0', 1), ('term1', 1)], list(docsetlist.termCardinalities(DocSet('', [0, 1]))))

        docsetlist.addDocument(1, ['term0', 'term1'])
        self.assertEquals('term0', docsetlist[0].term())
        self.assertEquals('term1', docsetlist[1].term())
        self.assertEquals([('term0', 2), ('term1', 2)], list(docsetlist.termCardinalities(DocSet('',[0, 1]))))

        docsetlist.addDocument(2, ['term0', 'term2'])
        self.assertEquals([('term0', 3), ('term1', 2), ('term2', 1)], list(docsetlist.termCardinalities(DocSet('',[0, 1, 2]))))

        try:
            docsetlist.addDocument(2, ['term0', 'term2'])
        except Exception, e:
            self.assertTrue("non-increasing" in str(e))

    def testDynamicDrilldownFields(self):
        self.addUntokenized([
            ('0', {'field_0': 'this is term_0', 'field_1': 'inquery'}),
            ('1', {'field_0': 'this is term_1', 'field_1': 'inquery'}),
            ('2', {'field_0': 'this is term_1', 'field_1': 'inquery'}),
            ('3', {'__private_field': 'this is term_2', 'field_1': 'cannotbefound'})])
        reader = IndexReader.open(self.tempdir)
        drilldown = Drilldown()
        drilldown.indexStarted(reader)
        docset = self.index.docsetFromQuery(MatchAllDocsQuery())
        results = list(drilldown.drilldown(docset, [('field_0', 0, False)]))
        self.assertEquals('field_0', results[0][0])
        results = list(drilldown.drilldown(docset))
        self.assertEquals('field_0', results[0][0])
        self.assertEquals('field_1', results[1][0])
        self.assertEquals(2, len(results))

    def testFieldGetAdded(self):
        self.addUntokenized([
            ('0', {'field_0': 'this is term_0'})
        ])
        drilldown = Drilldown()
        drilldown.indexStarted(self.index.getIndexReader())
        docset = self.index.docsetFromQuery(MatchAllDocsQuery())
        results = list(drilldown.drilldown(docset))
        self.assertEquals('field_0', results[0][0])
        self.assertEquals(1, len(results))
        self.addUntokenized([
            ('1', {'field_0': 'this is term_0', 'field_1': 'inquery'})
        ])
        drilldown.indexStarted(self.index.getIndexReader())
        docset = self.index.docsetFromQuery(MatchAllDocsQuery())
        results = list(drilldown.drilldown(docset))
        self.assertEquals(2, len(results))
        self.assertEquals('field_0', results[0][0])
        self.assertEquals('field_1', results[1][0])

    def testDrilldownFieldnames(self):
        d = DrilldownFieldnames(
            lookup=lambda name: 'drilldown.'+name,
            reverse=lambda name: name[len('drilldown.'):])
        observer = CallTrace('drilldown')
        observer.returnValues['drilldown'] = [('drilldown.field1', [('term1',1)]),('drilldown.field2', [('term2', 2)])]
        d.addObserver(observer)
        hits = CallTrace('Hits')

        result = list(d.drilldown(hits, [('field1', 0, True),('field2', 3, False)]))

        self.assertEquals(1, len(observer.calledMethods))
        self.assertEquals([('drilldown.field1', 0, True),('drilldown.field2', 3, False)], list(observer.calledMethods[0].args[1]))

        self.assertEquals([('field1', [('term1',1)]),('field2', [('term2', 2)])], result)

from time import sleep
class TimerForTestSupport(object):
    def addTimer(self, time, callback):
        callback()

        sleep(0.01)
        return (time,callback)
    def removeTimer(self, token):
        pass
