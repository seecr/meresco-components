# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009-2010 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2011 Maastricht University http://www.um.nl
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
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

from cq2utils import CQ2TestCase, CallTrace
from utils import asyncreturn
from testutils import generators2lists

from struct import calcsize

from meresco.components.facetindex.merescolucene import Term, TermQuery, IndexReader, MatchAllDocsQuery
from meresco.components.facetindex.document import Document
from meresco.components.facetindex.drilldown import Drilldown, NoFacetIndexException
from meresco.components.facetindex.lucene import LuceneIndex

from meresco.components.facetindex.docset import DocSet
from meresco.components.facetindex.docsetlist import DocSetList, JACCARD_ONLY

MACHINEBITS = calcsize('P') * 8

class DrilldownTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.index = LuceneIndex(self.tempdir)

    def tearDown(self):
        self.index.close()
        CQ2TestCase.tearDown(self)

    def createDrilldown(self, *args, **kwargs):
        self.drilldown = Drilldown(*args, **kwargs)
        self.index.addObserver(self.drilldown)
        self.index.observer_init()

    #Helper functions:
    def addUntokenized(self, documents, index=None):
        self.addToIndex(documents, index=index)

    def addTokenized(self, documents, index=None):
        self.addToIndex(documents, tokenize=True, index=index)

    def addToIndex(self, documents, tokenize=False, index=None):
        if not index:
            index = self.index

        for identifier, fields in documents:
            myDocument = Document(identifier)
            for field, value in fields.items():
                myDocument.addIndexedField(field, value, tokenize = tokenize)
            index.addDocument(myDocument)
        index.commit()
        if hasattr(self, 'drilldown'):
            self.drilldown.commit()

    def testIndexStarted(self):
        self.createDrilldown(['field_0'])
        self.addUntokenized([('id', {'field_0': 'this is term_0'})])

        results = self.doDrilldown(DocSet(data=[0]), [('field_0', 10, False)])
        field, termCounts = results[0]
        self.assertEquals('field_0', field)
        self.assertEquals([('this is term_0', 1)], list(termCounts))

    def testDrilldown(self):
        self.createDrilldown(['field_0', 'field_1'])
        self.addUntokenized([
            ('0', {'field_0': 'this is term_0', 'field_1': 'inquery'}),
            ('1', {'field_0': 'this is term_1', 'field_1': 'inquery'}),
            ('2', {'field_0': 'this is term_1', 'field_1': 'inquery'}),
            ('3', {'field_0': 'this is term_2', 'field_1': 'cannotbefound'})])
        query = TermQuery(Term("field_1", "inquery"))
        response = self.executeQuery(query)
        total, queryResults = response.total, response.hits
        self.assertEquals(3, total)
        self.assertEquals(['0', '1', '2'], queryResults)
        queryDocset = self.index.docsetFromQuery(query)
        drilldownResult = self.doDrilldown(queryDocset, [('field_0', 0, False), ('field_1', 0, False)])
        self.assertEquals(2, len(drilldownResult))
        result = dict(drilldownResult)
        self.assertEquals(['field_0', 'field_1'], result.keys())
        self.assertEquals(set([("this is term_0", 1), ("this is term_1", 2)]), set(result['field_0']))
        self.assertEquals([("inquery", 3)], list(result['field_1']))

    def testHierarchicalDrilldown(self):
        self.createDrilldown(['faculty', 'group'])
        self.addUntokenized([
            ('0', {'faculty': 'economie',    'group': 'accounting'}),
            ('1', {'faculty': 'geneeskunde', 'group': 'cardiologie'}),
            ('2', {'faculty': 'geneeskunde', 'group': 'cardiologie'}),
            ('3', {'faculty': 'geneeskunde', 'group': 'biochemie'}),
            ('4', {'faculty': 'economie',    'group': 'algemeen'}),
            ('5', {'faculty': 'economie',    'group': 'accounting'}),
            ('6', {'faculty': 'geneeskunde', 'group': 'algemeen'}),
            ('7', {'faculty': 'wiskunde',    'group': 'algemeen'}),
        ])
        queryDocset = self.index.docsetFromQuery(MatchAllDocsQuery())
        drilldownResults = self.drilldown.hierarchicalDrilldown(queryDocset, [(['faculty', 'group'], 2, False)])

        self.assertEquals([
            dict(fieldname='faculty', terms=[
                dict(term='economie', count=3, remainder=[
                    dict(fieldname='group', terms=[
                        dict(term='accounting', count=2, remainder=[]),
                        dict(term='algemeen',   count=1, remainder=[])
                    ])
                 ]),
                 dict(term='geneeskunde', count=4, remainder=[
                    dict(fieldname='group', terms=[
                        dict(term='algemeen', count=1, remainder=[]),
                        dict(term='biochemie', count=1, remainder=[]),
                    ])
                 ])
             ])
        ], generators2lists(drilldownResults))

    def testSortingOnCardinality(self):
        self.createDrilldown(['field0'])
        self.addUntokenized([
            ('0', {'field0': 'term1'}),
            ('1', {'field0': 'term1'}),
            ('2', {'field0': 'term2'}),
            ('3', {'field0': 'term0'})])
        hits = self.index.docsetFromQuery(MatchAllDocsQuery())
        ddData = self.doDrilldown(hits, [('field0', 0, False)])
        self.assertEquals([('term0',1), ('term1',2), ('term2',1)], list(ddData[0][1]))
        result = self.doDrilldown(hits, [('field0', 0, True)])
        self.assertEquals([('term1',2), ('term0',1), ('term2',1)], list(result[0][1]))

    def testDefaultSorting(self):
        self.createDrilldown(['field0'])
        self.addUntokenized([
            ('0', {'field0': 'term1'}),
            ('1', {'field0': 'term1'}),
            ('2', {'field0': 'term2'}),
            ('3', {'field0': 'term0'})])
        hits = self.index.docsetFromQuery(MatchAllDocsQuery())
        ddData = self.doDrilldown(hits, defaultSorting=False)
        self.assertEquals([('term0',1), ('term1',2), ('term2',1)], list(ddData[0][1]))
        result = self.doDrilldown(hits, defaultSorting=True)
        self.assertEquals([('term1',2), ('term0',1), ('term2',1)], list(result[0][1]))

    def testDefaultMaximumResults(self):
        self.createDrilldown(['field0'])
        self.addUntokenized([
            ('0', {'field0': 'term1'}),
            ('1', {'field0': 'term1'}),
            ('2', {'field0': 'term2'}),
            ('3', {'field0': 'term0'})])
        hits = self.index.docsetFromQuery(MatchAllDocsQuery())
        ddData = self.doDrilldown(hits, defaultMaximumResults=2)
        self.assertEquals([('term0',1), ('term1',2)], list(ddData[0][1]))

    def testDynamicDrilldownFields(self):
        self.createDrilldown(['*'])
        self.addUntokenized([
            ('0', {'field_0': 'this is term_0', 'field_1': 'inquery'}),
            ('1', {'field_0': 'this is term_1', 'field_1': 'inquery'}),
            ('2', {'field_0': 'this is term_1', 'field_1': 'inquery'}),
            ('3', {'__private_field': 'this is term_2', 'field_1': 'cannotbefound'})])
        docset = self.index.docsetFromQuery(MatchAllDocsQuery())
        results = self.doDrilldown(docset, [('field_0', 0, False)])
        self.assertEquals('field_0', results[0][0])
        results = self.doDrilldown(docset)
        self.assertEquals('field_0', results[0][0])
        self.assertEquals('field_1', results[1][0])
        self.assertEquals(2, len(results))

    def testFieldGetAdded(self):
        self.createDrilldown(['*'])
        self.addUntokenized([
            ('0', {'field_0': 'this is term_0'})
        ])
        docset = self.index.docsetFromQuery(MatchAllDocsQuery())
        results = self.doDrilldown(docset)
        self.assertEquals('field_0', results[0][0])
        self.assertEquals(1, len(results))
        self.addUntokenized([
            ('1', {'field_0': 'this is term_0', 'field_1': 'inquery'})
        ])
        docset = self.index.docsetFromQuery(MatchAllDocsQuery())
        results = self.doDrilldown(docset)
        self.assertEquals(2, len(results))
        self.assertEquals('field_0', results[0][0])
        self.assertEquals('field_1', results[1][0])

    def testJaccardIndex(self):
        self.createDrilldown(['title'])
        self.addTokenized([
            ('0', {'title': 'cats dogs mice'}),
            ('1', {'title': 'cats dogs'}),
            ('2', {'title': 'cats'}),
            ('3', {'title': 'dogs mice'})])
        # The following line fixes test, but in the wrong way
        #self.drilldown.indexStarted(self.index)

        query = TermQuery(Term("title", "dogs"))
        response = self.executeQuery(query)
        total, queryResults = response.total, response.hits
        queryDocset = self.index.docsetFromQuery(query)
        jaccardIndices = list(self.drilldown.jaccard(queryDocset, [("title", 0, 100)], algorithm=JACCARD_ONLY))
        self.assertEquals([('title', [('dogs',100),('mice', 66),('cats',50)])], list((fieldname, list(items)) for fieldname, items in jaccardIndices))

        jaccardIndices = list(self.drilldown.jaccard(queryDocset, [("title", 45, 55)], algorithm=JACCARD_ONLY))
        self.assertEquals([('title', [('cats',50)])], list((fieldname, list(items)) for fieldname, items in jaccardIndices))

    def testJaccardPassMaxTermFreqPercentage(self):
        drilldown = Drilldown([])
        drilldown._index = CallTrace('index', returnValues={'docCount':78})
        docSetList_for_title = CallTrace('DocSetList')
        drilldown._docsetlists['title'] = docSetList_for_title
        list(drilldown.jaccard(None, [("title", 17, 67)], maxTermFreqPercentage=80))
        algorithm = '<class c_int>' if MACHINEBITS == 64 else '<class c_long>'
        self.assertEquals("[jaccards(None, 17, 67, 78, algorithm=%s, maxTermFreqPercentage=80)]" % algorithm, str(docSetList_for_title.calledMethods))

    def testJaccardIndexChecksFields(self):
        self.createDrilldown(['title'])
        try:
            jaccardIndex = list(self.drilldown.jaccard(None, [("name", 0, 100)]))
            self.fail()
        except NoFacetIndexException, e:
            self.assertEquals("No facetindex for field 'name'. Available fields: 'title'", str(e))

    def testIsDrilldownField(self):
        drilldown = Drilldown()
        self.assertFalse(drilldown._isDrilldownField("thingy"))
        drilldown = Drilldown(drilldownFields=['*'])
        self.assertTrue(drilldown._isDrilldownField("thingy"))
        self.assertFalse(drilldown._isDrilldownField("__thingy"))
        drilldown = Drilldown(drilldownFields=['thing*'])
        self.assertTrue(drilldown._isDrilldownField("thingy"))
        drilldown = Drilldown(drilldownFields=['thingy'])
        self.assertTrue(drilldown._isDrilldownField("thingy"))
        drilldown = Drilldown(drilldownFields=[('thingy', )])
        self.assertTrue(drilldown._isDrilldownField(("thingy",)))

    def testAddDocument(self):
        drilldown = Drilldown(['title'])
        self.assertEquals(0, drilldown.queueLength())
        drilldown.addDocument(0, {'title': ['value']})
        self.assertEquals(2, drilldown.queueLength())

    def testDeleteDocumentFromQueue(self):
        drilldown = Drilldown(['title'])
        self.assertEquals(0, drilldown.queueLength())
        drilldown.deleteDocument(0)
        self.assertEquals(1, drilldown.queueLength())

    def testCommitClearsQueue(self):
        drilldown = Drilldown(['title'])
        drilldown.deleteDocument(0)
        drilldown.addDocument(0, {'title': ['value']})
        self.assertEquals(3, drilldown.queueLength())
        drilldown.commit()
        self.assertEquals(0, drilldown.queueLength())

        def raiseException(*args, **kwargs):
            raise Exception('Exception')
        drilldown._delete = raiseException
        drilldown.deleteDocument(0)
        try:
            drilldown.commit()
            self.fail()
        except Exception, e:
            self.assertEquals("Exception", str(e))
        self.assertEquals(0, drilldown.queueLength())

    def testCommit(self):
        drilldown = Drilldown(['title'])
        drilldown.addDocument(0, {'title': ['value']})
        drilldown.addDocument(1, {'title': ['value2']})

        self.assertEquals(0, len(drilldown._docsetlists['title']))
        drilldown.commit()
        self.assertEquals(0, drilldown.queueLength())
        self.assertEquals(2, len(drilldown._docsetlists['title']))
        self.assertEquals([('value', 1), ('value2', 1)], list(drilldown._docsetlists['title'].allCardinalities()))

        drilldown.deleteDocument(0)
        self.assertEquals(2, len(drilldown._docsetlists['title']))
        drilldown.commit()
        self.assertEquals(2, len(drilldown._docsetlists['title']))
        self.assertEquals([('value', 0), ('value2', 1)], list(drilldown._docsetlists['title'].allCardinalities()))

    def testMapLuceneIdsOnStartup(self):
        documents = []
        for i in range(8):
            recordId = 'id:%0.3d' % i
            data = {'field_0': 'value%0.3d' % i}
            documents.append((recordId, data))
        self.addUntokenized(documents)
        self.index.close()

        #print "---- 1 ----"
        index = LuceneIndex(self.tempdir)
        drilldown = Drilldown(['field_0'])
        drilldown.indexStarted(index)

        index.delete('id:003')
        index.delete('id:006')
        index.commit()
        drilldown.commit()
        index.close()

        #print "---- 2 ----"
        index2 = LuceneIndex(self.tempdir)
        drilldown2 = Drilldown(['field_0'])
        drilldown2.indexStarted(index2)
        documents = []
        for i in range(8,89):
            recordId = 'id:%0.3d' % i
            data = {'field_0': 'value%0.3d' % i}
            documents.append((recordId, data))
        self.addUntokenized(documents, index=index2)

        drilldown2.commit()
        index2.close()

        #print "---- 3 ----"
        index3 = LuceneIndex(self.tempdir)
        drilldown3 = Drilldown(['field_0'])
        drilldown3.indexStarted(index3)
        drilldownDocIds = [x[0] for x in list(drilldown3._docsetlists['field_0'])]

        self.assertEquals([0, 1, 2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88], drilldownDocIds)

    def testIntersect(self):
        self.createDrilldown(['field_0', 'field_1'])
        self.drilldown.addDocument(0, {'field_0': ['this is term_0'], 'field_1': ['inquery']})
        self.drilldown.addDocument(1, {'field_0': ['this is term_1'], 'field_1': ['inquery']})
        self.drilldown.addDocument(2, {'field_0': ['this is term_1'], 'field_1': ['inquery']})
        self.drilldown.addDocument(3, {'field_0': ['this is term_2'], 'field_1': ['cannotbefound']})
        self.drilldown.commit()
        dsl0 = self.drilldown.intersect('field_0', DocSet([0,1,2,3]))
        self.assertEquals([[0], [1,2], [3]], list(dsl0))
        dsl1 = self.drilldown.intersect('field_1', DocSet([0,1,2,3]))
        self.assertEquals([[0,1,2],[3]], list(dsl1))

    def testMultiFieldDrilldown(self):
        self.createDrilldown(['field_0', ('keyword', 'title'), 'field_1'])
        self.drilldown.addDocument(0, {'keyword': ['math'], 'title': ['mathematics for dummies']})
        self.drilldown.addDocument(1, {'keyword': ['economics'], 'description': ['cheating with numbers']})
        self.drilldown.commit()
        results = self.doDrilldown(DocSet([0,1]), [(('keyword', 'title'), 0, False)])
        self.assertEquals(('keyword', 'title'), results[0][0])
        resultTerms = list(results[0][1])
        self.assertEquals(set([('math', 1), ('mathematics for dummies', 1), ('economics', 1)]), set(resultTerms))

        # test order (cardinality)
        self.drilldown.addDocument(2, {'keyword': ['economics'], 'description': ['making a fortune of bad loans']})
        self.drilldown.addDocument(3, {'keyword': ['economics'], 'title': ['mathematics for dummies']})
        self.drilldown.commit()
        results = self.doDrilldown(DocSet([0,1,2,3]), [(('keyword', 'title'), 0, True)])
        resultTerms = list(results[0][1])
        self.assertEquals([('economics', 3), ('mathematics for dummies', 2), ('math', 1)], resultTerms)

    def testMultiFieldDrilldownWithRepeatedTerms(self):
        self.createDrilldown(['field_0', ('keyword', 'title'), 'field_1'])
        self.drilldown.addDocument(0, {'keyword': ['math'], 'title': ['mathematics for dummies']})
        self.drilldown.addDocument(1, {'keyword': ['economics'], 'description': ['cheating with numbers']})
        self.drilldown.addDocument(2, {'keyword': ['economics','economics'], 'title': ['ecocs']})
        self.drilldown.commit()
        results = self.doDrilldown(DocSet([0,1]), [(('keyword', 'title'), 0, False)])
        resultTerms = list(results[0][1])
        self.assertEquals(set([('math', 1), ('mathematics for dummies', 1), ('economics', 1)]), set(resultTerms))

    def testMultiFieldDrilldownAfterDelete(self):
        self.createDrilldown(['field_0', ('keyword', 'title'), 'field_1'])
        self.drilldown.addDocument(0, {'keyword': ['math'], 'title': ['mathematics for dummies']})
        self.drilldown.addDocument(1, {'keyword': ['economics'], 'description': ['cheating with numbers']})
        self.drilldown.commit()
        results = self.doDrilldown(DocSet([0,1]), [(('keyword', 'title'), 0, False)])
        resultTerms = list(results[0][1])
        self.assertEquals(set([('math', 1), ('mathematics for dummies', 1), ('economics', 1)]), set(resultTerms))

        self.drilldown.deleteDocument(1)
        self.drilldown.commit()
        results = self.doDrilldown(DocSet([0,1]), [(('keyword', 'title'), 0, False)])
        resultTerms = list(results[0][1])
        self.assertEquals(set([('math', 1), ('mathematics for dummies', 1)]), set(resultTerms))

    def testIndexStartedWithCompoundField(self):
        self.createDrilldown(['field_0', ('field_0', 'field_1')])
        self.addUntokenized([('id0', {'field_0': 'this is term_0'})])
        self.addUntokenized([('id1', {'field_1': 'this is term_1'})])

        results = self.doDrilldown(DocSet(data=[0,1]), [(('field_0', 'field_1'), 10, False)])
        field, termCounts = results[0]
        self.assertEquals(('field_0', 'field_1'), field)
        self.assertEquals([('this is term_0', 1), ('this is term_1', 1)], list(termCounts))

    def testCompoundFieldReusesPreviousDrilldown(self):
        self.createDrilldown(['field_0', ('field_0', 'field_1')])
        called = []
        def _docSetListFromTermEnumForField(field, indexReader, docIdMapping):
            called.append(field)
            return DocSetList()
        self.drilldown._docSetListFromTermEnumForField = _docSetListFromTermEnumForField
        index = CallTrace(name="index", returnValues=dict(getIndexReader=CallTrace(), getDocIdMapping=None))
        self.drilldown._determineDrilldownFields = lambda *args: ['field_0']
        self.drilldown.indexStarted(index)
        self.assertEquals(['field_0', 'field_1'], called)

    def testDetermineDrilldownFieldnamesWithoutStars(self):
        self.addUntokenized([('id0', {
            'prefix.field_0': 'this is term_0',
            'prefix.field_1': 'this is term_1',
            'field_2': 'this is term_2'})])
        drilldown = Drilldown(['field_2'])
        fields = drilldown._determineDrilldownFields(self.index.getIndexReader())
        self.assertEquals(set(['field_2']), fields)

    def testDetermineDrilldownFieldnamesWithAllstars(self):
        self.addUntokenized([('id0', {
            'prefix.field_0': 'this is term_0',
            'prefix.field_1': 'this is term_1',
            'field_2': 'this is term_2'})])
        drilldown = Drilldown(['*'])
        fields = drilldown._determineDrilldownFields(self.index.getIndexReader())
        self.assertEquals(set(['field_2', 'prefix.field_0', 'prefix.field_1']) , fields)

    def testDetermineDrilldownFieldnamesWithPrefixStar(self):
        self.addUntokenized([('id0', {
            'prefix.field_0': 'this is term_0',
            'prefix.field_1': 'this is term_1',
            'field_2': 'this is term_2'})])
        drilldown = Drilldown(['prefix.*'])
        fields = drilldown._determineDrilldownFields(self.index.getIndexReader())
        self.assertEquals(set(['prefix.field_0', 'prefix.field_1']) , fields)

    def testDrilldownFieldnamesWithPrefixStar(self):
        self.createDrilldown(['prefix.*'])
        self.addUntokenized([('id0', {
            'prefix.field_0': 'this is term_0',
            'prefix.field_1': 'this is term_1',
            'field_2': 'this is term_2'})])
        results = self.doDrilldown(DocSet(data=[0]), [('prefix.field_0', 10, False)])
        field, termCounts = results[0]
        self.assertEquals([('this is term_0', 1)], list(termCounts))

    def testCompoundFieldWithSameTermInDifferentFields(self):
        drilldown = Drilldown([('field_0', 'field_1')])
        drilldown._add(0, {'field_0': ['value'], 'field_1': ['value']}) # had a bug causing: "non-increasing docid" error

    def executeQuery(self, *args, **kwargs):
        return asyncreturn(self.index.executeQuery, *args, **kwargs)

    def doDrilldown(self, *args, **kwargs):
        return asyncreturn(self.drilldown.drilldown, *args, **kwargs)

