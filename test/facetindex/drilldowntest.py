# -*- coding: utf-8 -*-
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
from struct import calcsize
from merescocomponents.facetindex.merescolucene import Term, TermQuery, IndexReader, MatchAllDocsQuery

from cq2utils import CQ2TestCase, CallTrace

from merescocomponents.facetindex.document import Document
from merescocomponents.facetindex.drilldown import Drilldown, NoFacetIndexException
from merescocomponents.facetindex.drilldownfieldnames import DrilldownFieldnames
from merescocomponents.facetindex.lucene import LuceneIndex

from merescocomponents.facetindex.docset import DocSet
from merescocomponents.facetindex.docsetlist import DocSetList, JACCARD_ONLY

class DrilldownTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.index = LuceneIndex(self.tempdir)

    def tearDown(self):
        self.index.close()
        CQ2TestCase.tearDown(self)

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

    def testIndexStarted(self):
        self.addUntokenized([('id', {'field_0': 'this is term_0'})])

        drilldown = Drilldown(['field_0'])
        reader = IndexReader.open(self.tempdir)

        drilldown.indexStarted(reader, docIdMapping=self.index.getDocIdMapping())
        field, results = drilldown.drilldown(DocSet(data=[0]), [('field_0', 10, False)]).next()
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
        drilldown.indexStarted(reader, docIdMapping=self.index.getDocIdMapping())
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
        drilldown.indexStarted(reader, docIdMapping=self.index.getDocIdMapping())
        hits = self.index.docsetFromQuery(MatchAllDocsQuery())
        ddData = list(drilldown.drilldown(hits, [('field0', 0, False)]))
        self.assertEquals([('term0',1), ('term1',2), ('term2',1)], list(ddData[0][1]))
        result = list(drilldown.drilldown(hits, [('field0', 0, True)]))
        self.assertEquals([('term1',2), ('term0',1), ('term2',1)], list(result[0][1]))


    def testAppendToRow(self):
        docsetlist = DocSetList()
        docsetlist.addDocument(0, ['term0', 'term1'])
        self.assertEquals(set(['term0', 'term1']), set(docsetlist.termForDocset(docsetlist[i]) for i in range(2)))
        self.assertEquals([('term0', 1), ('term1', 1)], list(docsetlist.termCardinalities(DocSet([0, 1]))))
        docsetlist.addDocument(1, ['term0', 'term1'])
        self.assertEquals('term0', docsetlist.termForDocset(docsetlist[0]))
        self.assertEquals('term1', docsetlist.termForDocset(docsetlist[1]))
        self.assertEquals([('term0', 2), ('term1', 2)], list(docsetlist.termCardinalities(DocSet([0, 1]))))
        docsetlist.addDocument(2, ['term0', 'term2'])
        self.assertEquals([('term0', 3), ('term1', 2), ('term2', 1)], list(docsetlist.termCardinalities(DocSet([0, 1, 2]))))
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
        drilldown.indexStarted(reader, docIdMapping=self.index.getDocIdMapping())
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
        drilldown.indexStarted(self.index.getIndexReader(), docIdMapping=self.index.getDocIdMapping())
        docset = self.index.docsetFromQuery(MatchAllDocsQuery())
        results = list(drilldown.drilldown(docset))
        self.assertEquals('field_0', results[0][0])
        self.assertEquals(1, len(results))
        self.addUntokenized([
            ('1', {'field_0': 'this is term_0', 'field_1': 'inquery'})
        ])
        drilldown.indexStarted(self.index.getIndexReader(), docIdMapping=self.index.getDocIdMapping())
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

    def testJaccardIndex(self):
        self.addTokenized([
            ('0', {'title': 'cats dogs mice'}),
            ('1', {'title': 'cats dogs'}),
            ('2', {'title': 'cats'}),
            ('3', {'title': 'dogs mice'})])
        self.index._writer.flush()
        reader = IndexReader.open(self.tempdir)

        drilldown = Drilldown(['title'])
        drilldown.indexStarted(reader, docIdMapping=self.index.getDocIdMapping())
        query = TermQuery(Term("title", "dogs"))
        total, queryResults = self.index.executeQuery(query)
        queryDocset = self.index.docsetFromQuery(query)
        jaccardIndices = list(drilldown.jaccard(queryDocset, [("title", 0, 100)], algorithm=JACCARD_ONLY))
        self.assertEquals([('title', [('dogs',100),('mice', 66),('cats',50)])], list((fieldname, list(items)) for fieldname, items in jaccardIndices))

        jaccardIndices = list(drilldown.jaccard(queryDocset, [("title", 45, 55)], algorithm=JACCARD_ONLY))
        self.assertEquals([('title', [('cats',50)])], list((fieldname, list(items)) for fieldname, items in jaccardIndices))

    def testJaccardPassMaxTermFreqPercentage(self):
        drilldown = Drilldown([])
        drilldown._totaldocs = 78
        docSetList_for_title = CallTrace('DocSetList')
        drilldown._docsetlists['title'] = docSetList_for_title
        list(drilldown.jaccard(None, [("title", 17, 67)], maxTermFreqPercentage=80))
        self.assertEquals("[jaccards(None, 17, 67, 78, algorithm=<class c_int>, maxTermFreqPercentage=80)]", str(docSetList_for_title.calledMethods))

    def testJaccardIndexChecksFields(self):
        drilldown = Drilldown(['title'])
        try:
            jaccardIndex = list(drilldown.jaccard(None, [("name", 0, 100)]))
            self.fail()
        except NoFacetIndexException, e:
            self.assertEquals("No facetindex for field 'name'. Available fields: 'title'", str(e))

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
        reader = IndexReader.open(self.tempdir)
        drilldown = Drilldown(['title'])
        drilldown.indexStarted(reader, docIdMapping=self.index.getDocIdMapping())
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
        drilldown = Drilldown(['field_0'])
        self.index.addObserver(drilldown)
        documents = []
        for i in range(8):
            recordId = 'id:%0.3d' % i
            data = {'field_0': 'value%0.3d' % i}
            documents.append((recordId, data))
        self.addUntokenized(documents)
        drilldown.commit()
        self.index.close()

        #print "---- 1 ----"
        index = LuceneIndex(self.tempdir)
        drilldown = Drilldown(['field_0'])
        drilldown.indexStarted(index._reader, docIdMapping=index.getDocIdMapping())

        index.delete('id:003')
        index.delete('id:006')
        index.commit()
        drilldown.commit()
        index.close()

        #print "---- 2 ----"
        index2 = LuceneIndex(self.tempdir)
        drilldown2 = Drilldown(['field_0'])
        drilldown2.indexStarted(index2._reader, docIdMapping=index2.getDocIdMapping())
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
        drilldown3.indexStarted(index3._reader, docIdMapping=index3.getDocIdMapping())
        drilldownDocIds = [x[0] for x in list(drilldown3._docsetlists['field_0'])]

        self.assertEquals([0, 1, 2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88], drilldownDocIds)

    def testIntersect(self):
        drilldown = Drilldown(['field_0', 'field_1'])
        drilldown.addDocument(0, {'field_0': ['this is term_0'], 'field_1': ['inquery']})
        drilldown.addDocument(1, {'field_0': ['this is term_1'], 'field_1': ['inquery']})
        drilldown.addDocument(2, {'field_0': ['this is term_1'], 'field_1': ['inquery']})
        drilldown.addDocument(3, {'field_0': ['this is term_2'], 'field_1': ['cannotbefound']})
        drilldown.commit()
        dsl0 = drilldown.intersect('field_0', DocSet([0,1,2,3]))
        self.assertEquals([[0], [1,2], [3]], list(dsl0))
        dsl1 = drilldown.intersect('field_1', DocSet([0,1,2,3]))
        self.assertEquals([[0,2,1],[3]], list(dsl1))

    def testMultiFieldDrilldown(self):
        drilldown = Drilldown(['field_0', ('keyword', 'title'), 'field_1'])
        drilldown.addDocument(0, {'keyword': ['math'], 'title': ['mathematics for dummies']})
        drilldown.addDocument(1, {'keyword': ['economics'], 'description': ['cheating with numbers']})
        drilldown.commit()
        results = list(drilldown.drilldown(DocSet([0,1]), [(('keyword', 'title'), 0, False)]))
        self.assertEquals(('keyword', 'title'), results[0][0])
        resultTerms = list(results[0][1])
        self.assertEquals(set([('math', 1), ('mathematics for dummies', 1), ('economics', 1)]), set(resultTerms))

        # test order (cardinality)
        drilldown.addDocument(2, {'keyword': ['economics'], 'description': ['making a fortune of bad loans']})
        drilldown.addDocument(3, {'keyword': ['economics'], 'title': ['mathematics for dummies']})
        drilldown.commit()
        results = list(drilldown.drilldown(DocSet([0,1,2,3]), [(('keyword', 'title'), 0, True)]))
        resultTerms = list(results[0][1])
        self.assertEquals([('economics', 3), ('mathematics for dummies', 2), ('math', 1)], resultTerms)

    def testMultiFieldDrilldownWithRepeatedTerms(self):
        drilldown = Drilldown(['field_0', ('keyword', 'title'), 'field_1'])
        drilldown.addDocument(0, {'keyword': ['math'], 'title': ['mathematics for dummies']})
        drilldown.addDocument(1, {'keyword': ['economics'], 'description': ['cheating with numbers']})
        drilldown.addDocument(2, {'keyword': ['economics','economics'], 'title': ['ecocs']})
        drilldown.commit()
        results = list(drilldown.drilldown(DocSet([0,1]), [(('keyword', 'title'), 0, False)]))
        resultTerms = list(results[0][1])
        self.assertEquals(set([('math', 1), ('mathematics for dummies', 1), ('economics', 1)]), set(resultTerms))


    def testMultiFieldDrilldownAfterDelete(self):
        drilldown = Drilldown(['field_0', ('keyword', 'title'), 'field_1'])
        drilldown.addDocument(0, {'keyword': ['math'], 'title': ['mathematics for dummies']})
        drilldown.addDocument(1, {'keyword': ['economics'], 'description': ['cheating with numbers']})
        drilldown.commit()
        results = list(drilldown.drilldown(DocSet([0,1]), [(('keyword', 'title'), 0, False)]))
        resultTerms = list(results[0][1])
        self.assertEquals(set([('math', 1), ('mathematics for dummies', 1), ('economics', 1)]), set(resultTerms))

        drilldown.deleteDocument(1)
        drilldown.commit()
        results = list(drilldown.drilldown(DocSet([0,1]), [(('keyword', 'title'), 0, False)]))
        resultTerms = list(results[0][1])
        self.assertEquals(set([('math', 1), ('mathematics for dummies', 1)]), set(resultTerms))

    def testIndexStartedWithCompoundField(self):
        self.addUntokenized([('id0', {'field_0': 'this is term_0'})])
        self.addUntokenized([('id1', {'field_1': 'this is term_1'})])

        drilldown = Drilldown(['field_0', ('field_0', 'field_1')])
        reader = IndexReader.open(self.tempdir)

        drilldown.indexStarted(reader, docIdMapping=self.index.getDocIdMapping())
        field, results = drilldown.drilldown(DocSet(data=[0,1]), [(('field_0', 'field_1'), 10, False)]).next()
        self.assertEquals(('field_0', 'field_1'), field)
        self.assertEquals([('this is term_0', 1), ('this is term_1', 1)], list(results))

    def testCompoundFieldWithSameTermInDifferentFields(self):
        drilldown = Drilldown([('field_0', 'field_1')])
        drilldown._add(0, {'field_0': ['value'], 'field_1': ['value']}) # had a bug causing: "non-increasing docid" error

    def testGetIndexMeasure(self):
        machineBits = calcsize('P') * 8
        drilldown = Drilldown(['fld0', 'fld1', 'fld2'])
        measure = drilldown.measure()
        results = {
            32: {'dictionaries':1361047,'postings':0, 'terms':0, 'fields':3, 'totalBytes':120},
            64: {'dictionaries':1360874,'postings':0, 'terms':0, 'fields':3, 'totalBytes':144}
        }
        self.assertEquals(results[machineBits], measure)
        drilldown.addDocument(0, {'fld0':['t1','t2'],'fld1': ['t1','t3']})
        drilldown.addDocument(1, {'fld1':['t3','t4'],'fld2': ['t4','t5']})
        drilldown.commit()
        measure = drilldown.measure()
        results = {
            32: {'dictionaries':1361056,'postings':8, 'terms':7, 'fields':3, 'totalBytes':416},
            64: {'dictionaries':1360889,'postings':8, 'terms':7, 'fields':3, 'totalBytes':628}
        }
        self.assertEquals(results[machineBits], measure)
