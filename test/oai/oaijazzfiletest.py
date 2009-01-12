# -*- coding: utf-8 -*-
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

from os.path import isfile, join
from time import time

from merescocomponents.oai import OaiJazzFile

class OaiJazzFileTest(CQ2TestCase):
    #def setUp(self):
        #CQ2TestCase.setUp(self)
        #self.index = CallTrace("Index")
        #self.storage = CallTrace("Storage")
        #self.mockedjazz = OaiJazzLucene(self.index, self.storage, (i for i in xrange(100)))
        #self.id = "id"
        #self.partName = "xmlfields"
        #self.document = Xml2Document()._create(self.id, FIELDS)
        #self.realjazz = OaiJazzLucene(
            #LuceneIndex(
                #join(self.tempdir,'index'), timer=TimerForTestSupport()),
            #StorageComponent(join(self.tempdir,'storage')),
            #iter(xrange(99)))

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.jazz = OaiJazzFile(self.tempdir)
        self.stampNumber = 0
        def stamp():
            result = 1215313443000000 + self.stampNumber
            self.stampNumber += 1
            return result
        self.jazz._stamp = stamp

    #def tearDown(self):
        #self.realjazz.close()
        #CQ2TestCase.tearDown(self)

    def testOriginalStamp(self):
        jazz = OaiJazzFile(self.tempdir)
        stamps = [jazz._stamp() for i in xrange(1000)]
        self.assertEquals(list(sorted(set(stamps))), stamps)

    def testAddOaiRecordPrefixOnly(self):
        self.jazz.addOaiRecord(identifier='oai://1234?34', sets=[], metadataFormats=[('prefix', 'schema', 'namespace')])
        
        total, recordIds = self.jazz.oaiSelect(prefix='prefix')
        self.assertEquals(1, total)
        self.assertEquals(['oai://1234?34'], recordIds)

    def testAddOaiRecord(self):
        self.jazz.addOaiRecord('identifier', sets=[('setSpec', 'setName')], metadataFormats=[('prefix','schema', 'namespace')])
        self.assertEquals((1, ['identifier']), self.jazz.oaiSelect(prefix='prefix'))
        self.assertEquals((1, ['identifier']), self.jazz.oaiSelect(sets=['setSpec'],prefix='prefix'))
        self.assertEquals((0,[]), self.jazz.oaiSelect(sets=['unknown'],prefix='prefix'))

    def testAddOaiRecordWithNoSets(self):
        self.jazz.addOaiRecord('id1', sets=[], metadataFormats=[('prefix','schema', 'namespace')])
        self.jazz.addOaiRecord('id2', sets=[], metadataFormats=[('prefix','schema', 'namespace')])
        self.assertEquals((2, ['id1', 'id2']), self.jazz.oaiSelect(prefix='prefix'))

    def testAddOaiRecordWithNoMetadataFormats(self):
        try:
            self.jazz.addOaiRecord('identifier', sets=[('setSpec', 'setName')], metadataFormats=[])
            self.fail('Expected exception')
        except Exception, e:
            self.assertTrue('metadataFormat' in str(e), str(e))

    def testResultsStored(self):
        self.jazz.addOaiRecord(identifier='oai://1234?34', sets=[], metadataFormats=[('prefix', 'schema', 'namespace')])
        
        myJazz = OaiJazzFile(self.tempdir)

        total, recordIds = myJazz.oaiSelect(prefix='prefix')
        self.assertEquals(1, total)
        self.assertEquals(['oai://1234?34'], recordIds)

    def testGetFromMultipleSets(self):
        self.jazz.addOaiRecord('id1', sets=[('set1', 'set1name')], metadataFormats=[('prefix','schema', 'namespace')])
        self.jazz.addOaiRecord('id2', sets=[('set2', 'set2name')], metadataFormats=[('prefix','schema', 'namespace')])
        self.jazz.addOaiRecord('id3', sets=[('set3', 'set1name')], metadataFormats=[('prefix','schema', 'namespace')])
        self.assertEquals((2, ['id1','id2']), self.jazz.oaiSelect(sets=['set1','set2'], prefix='prefix'))

    def xtestPerformanceTestje(self):
        """This test is fast if storing on disk is off"""
        originalStore = self.jazz._store
        self.jazz._store = lambda:None
        t0 = time()
        for i in xrange(10000000):
            self.jazz.addOaiRecord('id%s' % i, sets=[('setSpec%s' % ((i / 100)*100), 'setName')], metadataFormats=[('prefix','schema', 'namespace')])
        t1 = time()
        #originalStore()
        t2 = time()
        total, ids = self.jazz.oaiSelect(sets=['setSpec95000'],prefix='prefix')
        self.assertEquals(100, total)
        print t1 - t0, t2 - t1, time() -t2
        # a set form 10 million records costs 3.9 seconds (Without any efficiency things applied
        # it costs 0.3 seconds with 1 million records
    
    def testListRecordsNoResults(self):
        total, result = self.jazz.oaiSelect(prefix='xxx')
        self.assertEquals([], result)
        self.assertEquals(0, total)

    def testUpdateOaiRecord(self):
        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix', 'schema', 'namespace')])
        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix', 'schema', 'namespace')])
        total, result = self.jazz.oaiSelect(prefix='prefix')
        self.assertEquals(1, total)
        self.assertEquals(['id:1'],result)
    
    def testUpdateOaiRecordSet(self):
        self.jazz.addOaiRecord('id:1', sets=[('setSpec1', 'setName1')], metadataFormats=[('prefix', 'schema', 'namespace')])
        
        total, result = self.jazz.oaiSelect(prefix='prefix', sets=['setSpec1'])
        self.assertEquals(1, total)

        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix', 'schema', 'namespace')])

        total, result = self.jazz.oaiSelect(prefix='prefix')
        self.assertEquals(1, total)
        self.assertEquals(['id:1'],result)
        
        total, result = self.jazz.oaiSelect(prefix='prefix', sets=['setSpec1'])
        self.assertEquals(0, total)

        self.assertEquals('', open(join(self.tempdir, 'sets', 'setSpec1')).read())

    def testAddPartWithUniqueNumbersAndSorting(self):
        self.jazz.addOaiRecord('123', metadataFormats=[('oai_dc', 'schema', 'namespace')])
        self.jazz.addOaiRecord('124', metadataFormats=[('lom', 'schema', 'namespace')])
        self.jazz.addOaiRecord('121', metadataFormats=[('lom', 'schema', 'namespace')])
        self.jazz.addOaiRecord('122', metadataFormats=[('lom', 'schema', 'namespace')])
        total, results = self.jazz.oaiSelect(prefix='oai_dc')
        self.assertEquals(1, total)
        total, results =self.jazz.oaiSelect(prefix='lom')
        self.assertEquals(3, total)
        self.assertEquals(['124', '121','122'], results)

    def testGetDatestampNotExisting(self):
        self.assertEquals(None, self.jazz.getDatestamp('doesNotExist'))

    def testGetDatestamp(self):
        self.jazz.addOaiRecord('123', metadataFormats=[('oai_dc', 'schema', 'namespace')])
        self.assertEquals('2008-07-06T05:04:03Z', self.jazz.getDatestamp('123'))

    def testDelete(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('oai_dc','schema', 'namespace')])
        self.assertFalse(self.jazz.isDeleted('42'))
        self.assertEquals((1, ['42']), self.jazz.oaiSelect(prefix='oai_dc'))
        self.jazz.delete('42')
        self.assertTrue(self.jazz.isDeleted('42'))
        self.assertEquals((1, ['42']), self.jazz.oaiSelect(prefix='oai_dc'))

    # delete nonExistingRecord
    # delete keeps the same identifier, sets, prefixes
    # delete and re-add
    # delete is persistent (written to a file.)

    # unique, for continueAt

    def xtestDeleteIncrementsDatestampAndUnique(self):
        self.jazz.addOaiRecord('23', metadataFormats=[('oai_dc','schema', 'namespace')])
        stamp = jazz.getDatestamp('23')
        #unique = jazz.getUnique('23')
        self.stampNumber += 1234567890 # increaseTime
        jazz.delete('23')
        self.assertNotEqual(stamp, jazz.getDatestamp('23'))
        #self.assertNotEquals(unique, int(jazz.getUnique('23')))

    #def testGetUnique(self):
        #self.index.ignoredAttributes=['isAvailable', 'getStream']
        #def getStream(id, partName):
            #yield """<oaimeta>
        #<stamp>DATESTAMP_FOR_TEST</stamp>
        #<unique>UNIQUE_FOR_TEST</unique>
		#<sets/>
		#<prefixes/>
    #</oaimeta>"""
        #self.storage.getStream = getStream
        #self.storage.isAvailable = lambda id, part: (True, True)
        #uniqueNumber = self.mockedjazz.getUnique('somedocid')
        #self.assertEquals('UNIQUE_FOR_TEST', uniqueNumber)

    #def testOaiSelectWithBatchSize(self):
        #jazz = self.realjazz
        #for i in range(123,143):
            #jazz.add('%s' % i, 'oai_dc', bind_string('<oai_dc/>'))
        #total, results =jazz.oaiSelect(prefix='oai_dc', batchSize=200)
        #self.assertEquals(20, total)
        #self.assertEquals(20, len(results))
        #total, results =jazz.oaiSelect(prefix='oai_dc', batchSize=2)
        #self.assertEquals(20, total)
        #self.assertEquals(2, len(results))
        
    
    #def testAddSetInfo(self):
        #header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>%s</setSpec></header>'
        #jazz = self.realjazz
        #jazz.add('123', 'oai_dc', bind_string(header % 1).header)
        #jazz.add('124', 'oai_dc', bind_string(header % 2).header)
        #total, results =jazz.oaiSelect(sets=['1'], prefix='oai_dc')
        #self.assertEquals(1, total)
        #total, results =jazz.oaiSelect(sets=['2'], prefix='oai_dc')
        #self.assertEquals(1, total)
        #total, results =jazz.oaiSelect(prefix='oai_dc')
        #self.assertEquals(2, total)

    #def testAddRecognizeNamespace(self):
        #header = '<header xmlns="this.is.not.the.right.ns"><setSpec>%s</setSpec></header>'
        #jazz = self.realjazz
        #jazz.add('123', 'oai_dc', bind_string(header % 1).header)
        #total, results =jazz.oaiSelect(sets=['1'], prefix='oai_dc')
        #self.assertEquals(0, total)
        #header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>%s</setSpec></header>'
        #jazz.add('124', 'oai_dc', bind_string(header % 1).header)
        #total, results =jazz.oaiSelect(sets=['1'], prefix='oai_dc')
        #self.assertEquals(1, total)

    #def testAddWithoutData(self):
        #jazz = self.realjazz
        #jazz.add('9', 'oai_cd', bind_string('<empty/>'))


    #def testMultipleHierarchicalSets(self):
        #spec = "<setSpec>%s</setSpec>"
        #header = '<header xmlns="http://www.openarchives.org/OAI/2.0/">%s</header>'
        #jazz = self.realjazz
        #jazz.add('124', 'oai_dc', bind_string(header % (spec % '2:3' + spec % '3:4')).header)
        #self.assertEquals((1,['124']), jazz.oaiSelect(sets=['2'], prefix='oai_dc'))
        #self.assertEquals((1,['124']), jazz.oaiSelect(sets=['2:3'], prefix='oai_dc'))
        #self.assertEquals((1,['124']), jazz.oaiSelect(sets=['3'], prefix='oai_dc'))
        #self.assertEquals((1,['124']), jazz.oaiSelect(sets=['3:4'], prefix='oai_dc'))

    #def testGetSets(self):
        #jazz = self.realjazz
        #header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>%s</setSpec></header>'
        #jazz.add('124', 'oai_dc', bind_string(header % 1).header)
        #sets = jazz.getSets('124')
        #self.assertEquals(['1'], sets)
        #header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>%s</setSpec></header>'
        #jazz.add('125', 'oai_dc', bind_string(header % 2).header)
        #sets = jazz.getSets('125')
        #self.assertEquals(['2'], sets)
        #header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>1:2</setSpec><setSpec>2</setSpec></header>'
        #jazz.add('124', 'oai_dc', bind_string(header).header)
        #sets = jazz.getSets('124')
        #self.assertEquals(['1', '1:2', '2'], sets)

    #def testSetSpecWithTokensSplit(self):
        #jazz = self.realjazz
        #header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>%s</setSpec></header>'
        #jazz.add('124', 'oai_dc', bind_string(header % "1:23").header)
        #total, results = jazz.oaiSelect(sets=['1:23'], prefix='oai_dc')
        #self.assertEquals(1, len(results))
        #self.assertEquals(1, total)

    #def testDeleteAndReAdd(self):
        #jazz = self.realjazz
        #header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>%s</setSpec></header>'
        #jazz.add('123', 'oai_dc', bind_string(header % "1").header)
        #jazz.delete('123')
        #jazz.add('123', 'oai_dc', bind_string(header % "1").header)
        #self.assertFalse(jazz.isDeleted('123'))

    #def testGetParts(self):
        #jazz = self.realjazz
        #jazz.add('123', 'oai_dc', bind_string('<dc/>').dc)
        #jazz.add('123', 'lom', bind_string('<lom/>').lom)
        #parts = jazz.getParts('123')
        #self.assertEquals(['oai_dc', 'lom'], parts)
        #self.assertEquals((1, ['123']), jazz.oaiSelect(prefix='lom'))
        #self.assertEquals((1, ['123']), jazz.oaiSelect(prefix='oai_dc'))

    #def testAddDocsWithSets(self):
        #jazz = self.realjazz
        #header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>%s</setSpec></header>'
        #jazz.add('456', 'oai_dc', bind_string(header % 'set1').header)
        #jazz.add('457', 'oai_dc', bind_string(header % 'set2').header)
        #jazz.add('458', 'oai_dc', bind_string(header % 'set3').header)
        #sets = jazz.listSets()
        #self.assertEquals(['set1', 'set2', 'set3'], sets)

    #def testHierarchicalSets(self):
        #jazz = self.realjazz
        #header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>%s</setSpec></header>'
        #jazz.add('456', 'oai_dc', bind_string(header % 'set1:set2:set3').header)
        #sets = jazz.listSets()
        #self.assertEquals(['set1', 'set1:set2', 'set1:set2:set3'], sorted(sets))

    #def testDatestamp(self):
        #jazz = self.realjazz
        #lower = strftime('%Y-%m-%dT%H:%M:%SZ', gmtime())
        #jazz.add('456', 'oai_dc', bind_string('<data/>'))
        #upper = strftime('%Y-%m-%dT%H:%M:%SZ', gmtime())
        #datestamp = jazz.getDatestamp('456')
        #self.assertTrue(lower <= datestamp <= upper, datestamp)

    #def testMetadataPrefixes(self):
        #jazz = self.realjazz
        #jazz.add('456', 'oai_dc', bind_string('<oai_dc:dc xmlns:oai_dc="http://oai_dc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
             #xsi:schemaLocation="http://oai_dc http://oai_dc/dc.xsd"/>').dc)
        #prefixes = jazz.getAllPrefixes()
        #self.assertEquals([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc')], list(prefixes))
        #jazz.add('457', 'dc2', bind_string('<oai_dc:dc xmlns:oai_dc="http://dc2"/>').dc)
        #prefixes = jazz.getAllPrefixes()
        #self.assertEquals(set([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc'), ('dc2', '', 'http://dc2')]), prefixes)

    #def testMetadataPrefixesFromRootTag(self):
        #jazz = self.realjazz
        #jazz.add('456', 'oai_dc', bind_string('<oai_dc:dc xmlns:oai_dc="http://oai_dc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
             #xsi:schemaLocation="http://oai_dc http://oai_dc/dc.xsd"/>'))
        #prefixes = jazz.getAllPrefixes()
        #self.assertEquals([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc')], list(prefixes))

    #def testIncompletePrefixInfo(self):
        #jazz = self.realjazz
        #jazz.add('457', 'dc2', bind_string('<oai_dc/>').oai_dc)
        #prefixes = jazz.getAllPrefixes()
        #self.assertEquals(set([('dc2', '', '')]), prefixes)

    #def testPreserveRicherPrefixInfo(self):
        #jazz = self.realjazz
        #jazz.add('457', 'oai_dc', bind_string('<oai_dc:dc xmlns:oai_dc="http://oai_dc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
             #xsi:schemaLocation="http://oai_dc http://oai_dc/dc.xsd"/>').dc)
        #jazz.add('457', 'oai_dc', bind_string('<oai_dc/>'))
        #prefixes = jazz.getAllPrefixes()
        #self.assertEquals(set([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc')]), prefixes)


    #def addDocuments(self, size):
        #for id in range(1,size+1):
            #self._addRecord(id)

    #def _addRecord(self, anId):
        #self.jazz.add('%05d' % anId, 'oai_dc', bind_string('<title>The Title %d</title>' % anId))

    #def testListAll(self):
        #self.addDocuments(1)
        #total, result = self.jazz.oaiSelect(prefix='oai_dc')
        #result2 = self.jazz.listAll()
        #self.assertEquals(['00001'], list(result2))
        #self.assertEquals(['00001'], result)

    #def testListRecordsWith2000(self):
        #BooleanQuery.setMaxClauseCount(10) # Cause an early TooManyClauses exception.
        #self.addDocuments(50)
        #total, result = self.jazz.oaiSelect(prefix='oai_dc')
        #self.assertEquals('00001', result[0])
        #total, result = self.jazz.oaiSelect(prefix='oai_dc', continueAt='%020d' % 1)
        #self.assertEquals('00002', result[0])

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

        #total, result = self.jazz.oaiSelect(prefix='oai_dc', oaiFrom="2007-09-22T00:00:00Z")
        #self.assertEquals(3, total)
        #total, result = self.jazz.oaiSelect(prefix='oai_dc', oaiFrom="2007-09-22", oaiUntil="2007-09-23")
        #self.assertEquals(2, total)

    #def testFixUntil(self):
        #self.assertEquals("2007-09-22T12:33:00Z", self.jazz._fixUntilDate("2007-09-22T12:33:00Z"))
        #self.assertEquals("2007-09-23T00:00:00Z", self.jazz._fixUntilDate("2007-09-22"))
        #self.assertEquals("2008-01-01T00:00:00Z", self.jazz._fixUntilDate("2007-12-31"))
        #self.assertEquals("2004-02-29T00:00:00Z", self.jazz._fixUntilDate("2004-02-28"))

#from time import sleep
#class TimerForTestSupport(object):
    #def addTimer(self, time, callback):
        #callback()

        #sleep(0.01)
        #return (time,callback)
    #def removeTimer(self, token):
        #pass
