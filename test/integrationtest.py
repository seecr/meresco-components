#!/usr/bin/env python
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

from os import system
from sys import path
from glob import glob
system('find .. -name "*.pyc" | xargs rm -f')

for aPath in glob('../deps.d/*'):
    path.insert(0, aPath)

path.insert(0, "..")

from unittest import main
from cq2utils import CQ2TestCase
from merescocomponents.facetindex import Drilldown, LuceneIndex, Document
from merescocore.framework import Observable, be, TransactionScope
from PyLucene import MatchAllDocsQuery

class IntegrationTest(CQ2TestCase):
    def testOne(self):
        index = LuceneIndex(self.tempdir, transactionName='document')
        drilldown = Drilldown(['generic1', 'generic2', 'generic3'], transactionName='document')
        server = be((Observable(),
            (TransactionScope('document'),
                (LuceneDocumentFromDict(),
                    (index,
                        (drilldown,)
                    )
                )
            )
        ))
        server.once.observer_init()
        def addRecord(number):
            server.do.addRecord('repository:record:id:%s' % number, {
                'generic1':'repository',
                'generic2': 'record:id:%04d' % number,
                'generic3': 'repositoryGroupId',
                'generic4': '2009-01-15',
                'generic5': 'Author'})

        for i in xrange(30):
            addRecord(i)
        server.do.deleteRecord('repository:record:id:12')


        for loopje in range(10):
            for i in xrange(15,20):
                addRecord(i)


        ds = index.docsetFromQuery(MatchAllDocsQuery())
        fieldname, sets = drilldown.drilldown(ds, [('generic1', 0, False)]).next()
        self.assertEquals('generic1', fieldname)
        self.assertEquals([('repository',29)], list(sets))

        fieldname, sets = drilldown.drilldown(ds, [('generic2', 0, False)]).next()
        self.assertEquals([('record:id:%04d' % i, 1) for i in range(30) if i != 12], list(sorted(sets)))


class LuceneDocumentFromDict(Observable):
    def addRecord(self, identifier, documentDict):
        d = Document(identifier)
        for k,v in documentDict.items():
            d.addIndexedField(k,v)
        self.do.addDocument(d)

    def deleteRecord(self, identifier):
        self.do.delete(identifier)


if __name__ == '__main__':
    main()
    os.system('find .. -name "*.pyc" | xargs rm -f')
