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
from cq2utils import CQ2TestCase, CallTrace

from merescocomponents.oai import OaiAddRecord
from amara.binderytools import bind_string

class OaiAddRecordTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.subject = OaiAddRecord()
        self.observer = CallTrace('observert')
        self.observer.getAllMetadataFormats = lambda: []
        self.subject.addObserver(self.observer)

    def testAdd(self):
        self.subject.add('id', 'partName', bind_string('<empty/>'))

        self.assertEquals(1,len(self.observer.calledMethods))
        self.assertEquals('addOaiRecord', self.observer.calledMethods[0].name)
        self.assertEquals('id', self.observer.calledMethods[0].kwargs['identifier'])
        self.assertEquals([('partName', '', '')], self.observer.calledMethods[0].kwargs['metadataFormats'])
        self.assertEquals(set(), self.observer.calledMethods[0].kwargs['sets'])

    def testAddSetInfo(self):
        header = bind_string('<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>1</setSpec></header>').header
        
        self.subject.add('123', 'oai_dc', header)
        
        self.assertEquals(1,len(self.observer.calledMethods))
        self.assertEquals('addOaiRecord', self.observer.calledMethods[0].name)
        self.assertEquals('123', self.observer.calledMethods[0].kwargs['identifier'])
        self.assertEquals([('oai_dc', '', "http://www.openarchives.org/OAI/2.0/")], self.observer.calledMethods[0].kwargs['metadataFormats'])
        self.assertEquals(set([('1','1')]), self.observer.calledMethods[0].kwargs['sets'])

    def testAddRecognizeNamespace(self):
        header = '<header xmlns="this.is.not.the.right.ns"><setSpec>%s</setSpec></header>'
        self.subject.add('123', 'oai_dc', bind_string(header % 1).header)
        header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>%s</setSpec></header>'
        self.subject.add('124', 'oai_dc', bind_string(header % 1).header)
        self.assertEquals([('oai_dc', '', "this.is.not.the.right.ns")], self.observer.calledMethods[0].kwargs['metadataFormats'])
        self.assertEquals([('oai_dc', '', "http://www.openarchives.org/OAI/2.0/")], self.observer.calledMethods[1].kwargs['metadataFormats'])

    def testMultipleHierarchicalSets(self):
        spec = "<setSpec>%s</setSpec>"
        header = '<header xmlns="http://www.openarchives.org/OAI/2.0/">%s</header>'
        self.subject.add('124', 'oai_dc', bind_string(header % (spec % '2:3' + spec % '3:4')).header)
        self.assertEquals('124', self.observer.calledMethods[0].kwargs['identifier'])
        self.assertEquals([('oai_dc', '', "http://www.openarchives.org/OAI/2.0/")], self.observer.calledMethods[0].kwargs['metadataFormats'])
        self.assertEquals(set([('2:3', '2:3'), ('3:4', '3:4')]), self.observer.calledMethods[0].kwargs['sets'])
    
    def testMetadataPrefixes(self):
        self.subject.add('456', 'oai_dc', bind_string('<oai_dc:dc xmlns:oai_dc="http://oai_dc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
             xsi:schemaLocation="http://oai_dc http://oai_dc/dc.xsd"/>').dc)
        self.assertEquals([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc')], self.observer.calledMethods[0].kwargs['metadataFormats'])
        self.subject.add('457', 'dc2', bind_string('<oai_dc:dc xmlns:oai_dc="http://dc2"/>').dc)
        self.assertEquals([('dc2', '', 'http://dc2')], self.observer.calledMethods[1].kwargs['metadataFormats'])

    def testMetadataPrefixesFromRootTag(self):
        self.subject.add('456', 'oai_dc', bind_string('<oai_dc:dc xmlns:oai_dc="http://oai_dc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
             xsi:schemaLocation="http://oai_dc http://oai_dc/dc.xsd"/>'))
        self.assertEquals([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc')], self.observer.calledMethods[0].kwargs['metadataFormats'])

    def testIncompletePrefixInfo(self):
        self.subject.add('457', 'dc2', bind_string('<oai_dc/>').oai_dc)
        self.assertEquals([('dc2', '', '')], self.observer.calledMethods[0].kwargs['metadataFormats'])

    #def testPreserveRicherPrefixInfo(self):
        #jazz = self.realjazz
        #jazz.add('457', 'oai_dc', bind_string('<oai_dc:dc xmlns:oai_dc="http://oai_dc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
             #xsi:schemaLocation="http://oai_dc http://oai_dc/dc.xsd"/>').dc)
        #jazz.add('457', 'oai_dc', bind_string('<oai_dc/>'))
        #prefixes = jazz.getAllMetadataFormats()
        #self.assertEquals(set([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc')]), prefixes)


#class OaiJazzLuceneIntegrationTest(CQ2TestCase):
    #def setUp(self):
        #CQ2TestCase.setUp(self)
        #self._luceneIndex = LuceneIndex(join(self.tempdir, "lucene-index"), timer=TimerForTestSupport())
        #self._storage = StorageComponent(join(self.tempdir,'storage'))
        #self.jazz = OaiJazzLucene(self._luceneIndex, self._storage, iter(xrange(9999)))

    #def addDocuments(self, size):
        #for id in range(1,size+1):
            #self._addRecord(id)

    #def _addRecord(self, anId):
        #self.jazz.add('%05d' % anId, 'oai_dc', bind_string('<title>The Title %d</title>' % anId))

    #def testListAll(self):
        #self.addDocuments(1)
        #result = self.jazz.oaiSelect(prefix='oai_dc')
        #result2 = self.jazz.listAll()
        #self.assertEquals(['00001'], list(result2))
        #self.assertEquals(['00001'], list(result))

    #def testListRecordsWith2000(self):
        #BooleanQuery.setMaxClauseCount(10) # Cause an early TooManyClauses exception.
        #self.addDocuments(50)
        #result = self.jazz.oaiSelect(prefix='oai_dc')
        #self.assertEquals('00001', result.next())
        #result = self.jazz.oaiSelect(prefix='oai_dc', continueAt='%020d' % 1)
        #self.assertEquals('00002', result.next())

    #def testListRecordsWithFromAndUntil(self):
        #BooleanQuery.setMaxClauseCount(10) # Cause an early TooManyClauses exception.
        #self.jazz._gettime = lambda: (2007, 9, 24, 14, 27, 53, 0, 267, 0)
        #self._addRecord(1)
        #self.jazz._gettime = lambda: (2007, 9, 23, 14, 27, 53, 0, 267, 0)
        #self._addRecord(2)
        #self.jazz._gettime = lambda: (2007, 9, 22, 14, 27, 53, 0, 267, 0)
        #self._addRecord(3)
        #self.jazz._gettime = lambda: (2007, 9, 21, 14, 27, 53, 0, 267, 0)
        #self._addRecord(4)

        #result = self.jazz.oaiSelect(prefix='oai_dc', oaiFrom="2007-09-22T00:00:00Z")
        #self.assertEquals(3, len(list(result)))
        #result = self.jazz.oaiSelect(prefix='oai_dc', oaiFrom="2007-09-22", oaiUntil="2007-09-23")
        #self.assertEquals(2, len(list(result)))

    #def testFixUntil(self):
        #self.assertEquals("2007-09-22T12:33:00Z", self.jazz._fixUntilDate("2007-09-22T12:33:00Z"))
        #self.assertEquals("2007-09-23T00:00:00Z", self.jazz._fixUntilDate("2007-09-22"))
        #self.assertEquals("2008-01-01T00:00:00Z", self.jazz._fixUntilDate("2007-12-31"))
        #self.assertEquals("2004-02-29T00:00:00Z", self.jazz._fixUntilDate("2004-02-28"))

    #def testOaiAddRecord(self):
        #self.jazz.OaiAddRecord('identifier', sets=[('setSpec', 'setName')], metadataFormats=[('prefix','schema', 'namespace')])
        #result = self.jazz.listAll()
        #self.assertEquals(['identifier'], list(result))
        #self.assertEquals(['identifier'], list(self.jazz.oaiSelect(prefix='prefix')))
        #self.assertEquals(['identifier'], list(self.jazz.oaiSelect(sets=['setSpec'],prefix='prefix')))
        #self.assertEquals([], list(self.jazz.oaiSelect(sets=['unknown'],prefix='prefix')))

    #def testOaiAddRecordWithNoSets(self):
        #self.jazz.OaiAddRecord('id1', sets=[], metadataFormats=[('prefix','schema', 'namespace')])
        #self.jazz.OaiAddRecord('id2', sets=[], metadataFormats=[('prefix','schema', 'namespace')])
        #self.assertEquals(['id1', 'id2'], list(self.jazz.oaiSelect(prefix='prefix')))

    #def testOaiAddRecordWithNoMetadataFormats(self):
        #try:
            #self.jazz.OaiAddRecord('identifier', sets=[('setSpec', 'setName')], metadataFormats=[])
            #self.fail()
        #except Exception, e:
            #self.assertTrue('metadataFormat' in str(e))

    #def testGetFromMultipleSets(self):
        #self.jazz.OaiAddRecord('id1', sets=[('set1', 'set1name')], metadataFormats=[('prefix','schema', 'namespace')])
        #self.jazz.OaiAddRecord('id2', sets=[('set2', 'set2name')], metadataFormats=[('prefix','schema', 'namespace')])
        #self.jazz.OaiAddRecord('id3', sets=[('set3', 'set1name')], metadataFormats=[('prefix','schema', 'namespace')])
        #self.assertEquals(['id1','id2'], list(self.jazz.oaiSelect(sets=['set1','set2'], prefix='prefix')))

from time import sleep
class TimerForTestSupport(object):
    def addTimer(self, time, callback):
        callback()

        sleep(0.01)
        return (time,callback)
    def removeTimer(self, token):
        pass
