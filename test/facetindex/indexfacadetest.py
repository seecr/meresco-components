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
from PyLucene import MatchAllDocsQuery
from merescocomponents.facetindex import LuceneIndex2, Document2
from merescocomponents.facetindex import LuceneDocIdTrackerDecorator
from cq2utils import CQ2TestCase, CallTrace

from merescocomponents.facetindex import IndexFacade


class IndexFacadeTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.index = LuceneIndex2(self.tempdir, CallTrace('timer'))
        tracker = LuceneDocIdTrackerDecorator(self.index)
        self.facade = IndexFacade(self.index)

    def testAddBatches(self):
        doc1 = Document2('id0')
        doc1.addIndexedField('field0', 'term0')
        self.facade.addDocument(doc1)
        self.assertEquals(0, len(self.facade.executeQuery(MatchAllDocsQuery())))
        self.assertEquals(0, len(self.index.executeQuery(MatchAllDocsQuery())))
        self.facade.flush()
        self.assertEquals(1, len(self.facade.executeQuery(MatchAllDocsQuery())))
        self.assertEquals(1, len(self.index.executeQuery(MatchAllDocsQuery())))

    def testDelete(self):
        doc0 = Document2('id0')
        doc0.addIndexedField('field0', 'term0')
        self.facade.addDocument(doc0)
        self.facade.flush()
        self.facade.delete('id0')
        self.assertEquals(1, len(self.facade.executeQuery(MatchAllDocsQuery())))
        self.facade.flush()
        self.assertEquals(0, len(self.facade.executeQuery(MatchAllDocsQuery())))

    def testDeleteIsSmart(self):
        self.index.delete = lambda anId: "should not reach here"+0
        doc0 = Document2('id0')
        doc0.addIndexedField('field0', 'term0')
        self.facade.addDocument(doc0)
        self.facade.delete('id0')
        self.assertEquals(0, len(self.facade.executeQuery(MatchAllDocsQuery())))
        self.facade.flush()
        self.assertEquals(0, len(self.facade.executeQuery(MatchAllDocsQuery())))
