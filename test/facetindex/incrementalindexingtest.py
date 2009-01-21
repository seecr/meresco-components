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

from cq2utils import CQ2TestCase
from merescocomponents.facetindex import LuceneIndex, Drilldown, Document
from PyLucene import MatchAllDocsQuery

class IncrementalIndexingTest(CQ2TestCase):

    def testOne(self):
        index = LuceneIndex(self.tempdir)
        drilldown = Drilldown(['field0'])
        index.addObserver(drilldown)
        index.start()
        doc = Document('1')
        doc.addIndexedField('field0', 'term0')
        index.addDocument(doc)
        index.commit()
        drilldown.commit()
        docset = index.docsetFromQuery(MatchAllDocsQuery())
        result = list(drilldown.drilldown(docset, [('field0', 0, False)]))
        self.assertEquals([('term0',1)], list(result[0][1]))
        index.delete('1')
        index.commit()
        drilldown.commit()
        docset = index.docsetFromQuery(MatchAllDocsQuery())
        result = list(drilldown.drilldown(docset, [('field0', 0, False)]))
        self.assertEquals([], list(result[0][1]))

        for identifier in xrange(30):
            doc = Document(str(identifier))
            doc.addIndexedField('field0', 'term0')
            index.addDocument(doc)
            index.commit()
            drilldown.commit()

        index.delete('12')
        index.commit()
        drilldown.commit()

        docset = index.docsetFromQuery(MatchAllDocsQuery())
        result = list(drilldown.drilldown(docset, [('field0', 0, False)]))
        sets = list(result[0][1])
        self.assertEquals([('term0', 29)], list(sorted(sets)))
