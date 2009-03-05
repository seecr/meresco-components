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

from cq2utils import CQ2TestCase
from merescocomponents.facetindex import LuceneIndex, Drilldown, Document
from PyLucene import MatchAllDocsQuery

class IncrementalIndexingTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.index = LuceneIndex(self.tempdir)
        self.drilldown = Drilldown(['field0'])
        self.index.addObserver(self.drilldown)
        self.index.start()

    def addDocument(self, identifier, **fields):
        doc = Document(identifier)
        for field, value in fields.items():
            doc.addIndexedField(field, value)
        self.index.addDocument(doc)

    def testOne(self):
        self.addDocument('1', field0='term0')
        self.index.commit()
        self.drilldown.commit()
        docset = self.index.docsetFromQuery(MatchAllDocsQuery())
        result = list(self.drilldown.drilldown(docset, [('field0', 0, False)]))
        self.assertEquals([('term0',1)], list(result[0][1]))
        self.index.delete('1')
        self.index.commit()
        self.drilldown.commit()
        docset = self.index.docsetFromQuery(MatchAllDocsQuery())
        result = list(self.drilldown.drilldown(docset, [('field0', 0, False)]))
        self.assertEquals([], list(result[0][1]))

        for identifier in xrange(30):
            self.addDocument(str(identifier), field0='term0')
            self.index.commit()
            self.drilldown.commit()

        self.index.delete('12')
        self.index.commit()
        self.drilldown.commit()

        docset = self.index.docsetFromQuery(MatchAllDocsQuery())
        result = list(self.drilldown.drilldown(docset, [('field0', 0, False)]))
        sets = list(result[0][1])
        self.assertEquals([('term0', 29)], list(sorted(sets)))

    def testSingleDeleteOfDocumentNotIndex(self):
        self.index.delete('1')
        self.assertEquals(0, self.index.queueLength())

    def testSingleDeleteOfDocumentInIndex(self):
        self.addDocument('1', field0='term0')
        self.index.commit()
        self.drilldown.commit()

        self.assertEquals(0, self.index.queueLength())
        self.assertEquals(0, self.drilldown.queueLength())
        self.index.delete('1')
        self.assertEquals(1, self.index.queueLength())
        self.assertEquals(['_delete'], [command.methodName() for command in self.index._commandQueue])
        self.assertEquals(1, self.drilldown.queueLength())
        self.assertEquals(['_delete'], [command.methodName() for command in self.drilldown._commandQueue])

    def testAddDocument(self):
        self.assertEquals(0, self.index.queueLength())
        self.assertEquals(0, self.drilldown.queueLength())
        self.addDocument('1', field0='term0')
        self.assertEquals(1, self.index.queueLength())     # add
        self.assertEquals(['_add'], [command.methodName() for command in self.index._commandQueue])
        self.assertEquals(2, self.drilldown.queueLength()) # delete, add
        self.assertEquals([
            '_delete(docId=0)',
            "_add(docDict={u'field0': [u'term0'], u'__id__': [u'1']}, docId=0)",
            ], list(repr(command) for command in self.drilldown._commandQueue))

    def testAddDocumentAndThenDeleteIt(self):
        self.assertEquals(0, self.index.queueLength())
        self.assertEquals(0, self.drilldown.queueLength())
        self.addDocument('1', field0='term0') # internally: add, delegated to drilldown
        self.index.delete('1')                # internally: delete, delegated to drilldown
        self.assertEquals(2, self.index.queueLength())     # add, delete
        self.assertEquals(['_add', '_delete'], [command.methodName() for command in self.index._commandQueue])
        #self.assertEquals(2, self.drilldown.queueLength()) # add, delete
        self.assertEquals([
            '_delete(docId=0)',
            "_add(docDict={u'field0': [u'term0'], u'__id__': [u'1']}, docId=0)",
            '_delete(docId=0)'], list(repr(command) for command in self.drilldown._commandQueue))

    def testDeleteDocumentAndThenAddIt(self):
        self.addDocument('1', field0='term0')
        self.index.commit()
        self.drilldown.commit()
        self.assertEquals(0, self.index.queueLength())
        self.assertEquals(0, self.drilldown.queueLength())
        self.index.delete('1')
        self.addDocument('1', field0='term0') # re-add: delete + add
        self.assertEquals(['_delete', '_add'], [command.methodName() for command in self.index._commandQueue])
        self.assertEquals(['_delete', '_delete', '_add'],
            [command.methodName() for command in self.drilldown._commandQueue])

    def addAndCommit(self, identifier):
        self.addDocument(identifier, field0='term0')
        self.index.commit()
        self.drilldown.commit()

    def testMultipleAdds(self):
        from random import randint
        for i in range(200):
            self.addAndCommit(str(randint(1,10)))
        for i in range(200):
            self.addAndCommit(str(randint(1,10)))

    def testDoNotDelegatePrivateDelete(self):
        self.addDocument('1', field0='term0') # internally: add
        self.index.commit()
        self.addDocument('1', field0='term0') # internally: delete, add
        self.index.commit()
        # now drilldown only contains his own delete/add sequence twice
        self.assertEquals(['_delete', '_add', '_delete', '_add'],
            [command.methodName() for command in self.drilldown._commandQueue])

    def testDeleteOfDocumentInQueueFindsTheRightDocument(self):
        self.addDocument('1', field0='term0') # docId 0
        self.addDocument('2', field0='term0') # dodId 1
        self.index.delete('2')                # looks for doc '2' in queue => delete 1
        self.index.commit()
        self.assertEquals('_delete(docId=1)', str(self.drilldown._commandQueue[-1]))