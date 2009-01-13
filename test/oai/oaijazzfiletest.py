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
from time import time, mktime

from merescocomponents.oai import OaiJazzFile
from merescocomponents.oai.oailist import OaiList, BATCH_SIZE
from merescocomponents.oai.oaijazzfile import _flattenSetHierarchy
from StringIO import StringIO
from lxml.etree import parse

class OaiJazzFileTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.jazz = OaiJazzFile(self.tempdir)
        self.stampNumber = 1215313443000000
        def stamp():
            result = self.stampNumber
            self.stampNumber += 1
            return result
        self.jazz._stamp = stamp

    def testOriginalStamp(self):
        jazz = OaiJazzFile(self.tempdir)
        stamps = [jazz._stamp() for i in xrange(1000)]
        self.assertEquals(list(sorted(set(stamps))), stamps)
        
    def testAddOaiRecordPrefixOnly(self):
        self.jazz.addOaiRecord(identifier='oai://1234?34', sets=[], metadataFormats=[('prefix', 'schema', 'namespace')])
        
        recordIds = self.jazz.oaiSelect(prefix='prefix')
        self.assertEquals(['oai://1234?34'], list(recordIds))

    def testAddOaiRecord(self):
        self.jazz.addOaiRecord('identifier', sets=[('setSpec', 'setName')], metadataFormats=[('prefix','schema', 'namespace')])
        self.assertEquals(['identifier'], list(self.jazz.oaiSelect(prefix='prefix')))
        self.assertEquals(['identifier'], list(self.jazz.oaiSelect(sets=['setSpec'],prefix='prefix')))
        self.assertEquals([], list(self.jazz.oaiSelect(sets=['unknown'],prefix='prefix')))

    def testAddOaiRecordWithNoSets(self):
        self.jazz.addOaiRecord('id1', sets=[], metadataFormats=[('prefix','schema', 'namespace')])
        self.jazz.addOaiRecord('id2', sets=[], metadataFormats=[('prefix','schema', 'namespace')])
        self.assertEquals(['id1', 'id2'], list(self.jazz.oaiSelect(prefix='prefix')))

    def testAddOaiRecordWithNoMetadataFormats(self):
        try:
            self.jazz.addOaiRecord('identifier', sets=[('setSpec', 'setName')], metadataFormats=[])
            self.fail('Expected exception')
        except Exception, e:
            self.assertTrue('metadataFormat' in str(e), str(e))

    def testResultsStored(self):
        self.jazz.addOaiRecord(identifier='oai://1234?34', sets=[], metadataFormats=[('prefix', 'schema', 'namespace')])
        
        myJazz = OaiJazzFile(self.tempdir)

        recordIds = myJazz.oaiSelect(prefix='prefix')
        self.assertEquals('oai://1234?34', recordIds.next())

    def testGetFromMultipleSets(self):
        self.jazz.addOaiRecord('id1', sets=[('set1', 'set1name')], metadataFormats=[('prefix','schema', 'namespace')])
        self.jazz.addOaiRecord('id2', sets=[('set2', 'set2name')], metadataFormats=[('prefix','schema', 'namespace')])
        self.jazz.addOaiRecord('id3', sets=[('set3', 'set1name')], metadataFormats=[('prefix','schema', 'namespace')])
        self.assertEquals(['id1','id2'], list(self.jazz.oaiSelect(sets=['set1','set2'], prefix='prefix')))

    def xtestPerformanceTestje(self):
        """This test is fast if storing on disk is off"""
        originalStore = self.jazz._store
        self.jazz._store = lambda:None
        t0 = time()
        for i in xrange(1 * 10**7):
            self.jazz.addOaiRecord('id%s' % i, sets=[('setSpec%s' % ((i / 100)*100), 'setName')], metadataFormats=[('prefix','schema', 'namespace')])
        t1 = time()
        ids = self.jazz.oaiSelect(sets=['setSpec95000'],prefix='prefix')
        firstId = ids.next()
        t2 = time()
        self.assertEquals(99, len(list(ids)))
        print t1 - t0, t2 - t1, time() -t2, time() -t1
        # a set form 10 million records costs 3.9 seconds (Without any efficiency things applied
        # it costs 0.3 seconds with 1 million records
        # retimed it at 2009-01-13:
        #  1 * 10**6 oaiSelect took 3.7 seconds
        #  1 * 10**7 oaiSelect took 37.3 seconds
        # after adding low, high for sets: although this quite optimal for this test!!
        #  1 * 10**6 oaiSelect took 0.071
        #  1 * 10**7 oaiSelect took 0.071
        # the above optimization is removed again, it was only there to show optimization could help  A LOT!
        
    
    def testListRecordsNoResults(self):
        result = self.jazz.oaiSelect(prefix='xxx')
        self.assertEquals([], list(result))

    def testUpdateOaiRecord(self):
        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix', 'schema', 'namespace')])
        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix', 'schema', 'namespace')])
        result = self.jazz.oaiSelect(prefix='prefix')
        self.assertEquals(['id:1'],list(result))
    
    def testUpdateOaiRecordSet(self):
        self.jazz.addOaiRecord('id:1', sets=[('setSpec1', 'setName1')], metadataFormats=[('prefix', 'schema', 'namespace')])
        
        result = self.jazz.oaiSelect(prefix='prefix', sets=['setSpec1'])
        self.assertEquals(1, len(list(result)))

        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix', 'schema', 'namespace')])

        result = self.jazz.oaiSelect(prefix='prefix')
        self.assertEquals(['id:1'],list(result))
        
        result = self.jazz.oaiSelect(prefix='prefix', sets=['setSpec1'])
        self.assertEquals(0, len(list(result)))

        self.assertEquals('', open(join(self.tempdir, 'sets', 'setSpec1.stamps')).read())

    def testAddPartWithUniqueNumbersAndSorting(self):
        self.jazz.addOaiRecord('123', metadataFormats=[('oai_dc', 'schema', 'namespace')])
        self.jazz.addOaiRecord('124', metadataFormats=[('lom', 'schema', 'namespace')])
        self.jazz.addOaiRecord('121', metadataFormats=[('lom', 'schema', 'namespace')])
        self.jazz.addOaiRecord('122', metadataFormats=[('lom', 'schema', 'namespace')])
        results = self.jazz.oaiSelect(prefix='oai_dc')
        self.assertEquals(['123'], list(results))
        results =self.jazz.oaiSelect(prefix='lom')
        self.assertEquals(['124', '121','122'], list(results))

    def testGetDatestampNotExisting(self):
        self.assertEquals(None, self.jazz.getDatestamp('doesNotExist'))

    def testGetDatestamp(self):
        self.jazz.addOaiRecord('123', metadataFormats=[('oai_dc', 'schema', 'namespace')])
        self.assertEquals('2008-07-06T05:04:03Z', self.jazz.getDatestamp('123'))

    def testDelete(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('oai_dc','schema', 'namespace')])
        self.assertFalse(self.jazz.isDeleted('42'))
        self.assertEquals(['42'], list(self.jazz.oaiSelect(prefix='oai_dc')))
        self.jazz.delete('42')
        self.assertTrue(self.jazz.isDeleted('42'))
        self.assertEquals(['42'], list(self.jazz.oaiSelect(prefix='oai_dc')))

    def testDeleteNonExistingRecords(self):
        self.jazz.addOaiRecord('existing', metadataFormats=[('prefix','schema', 'namespace')])
        self.jazz.delete('notExisting')
        self.assertEquals(['1215313443000000 existing\n'], open(join(self.tempdir, 'identifiers')).readlines())

    def testDeleteKeepsSetsAndPrefixes(self):
        self.jazz.addOaiRecord('42', sets=[('setSpec1', 'setName1'),('setSpec2', 'setName2')], metadataFormats=[('prefix1','schema', 'namespace'), ('prefix2','schema', 'namespace')])
        self.jazz.delete('42')
        self.assertEquals(['42'], list(self.jazz.oaiSelect(prefix='prefix1')))
        self.assertEquals(['42'], list(self.jazz.oaiSelect(prefix='prefix2')))
        self.assertEquals(['42'], list(self.jazz.oaiSelect(prefix='prefix1', sets=['setSpec1'])))
        self.assertEquals(['42'], list(self.jazz.oaiSelect(prefix='prefix1', sets=['setSpec2'])))
        self.assertEquals(['42'], list(self.jazz.oaiSelect(prefix='prefix2', sets=['setSpec2'])))
        self.assertTrue(self.jazz.isDeleted('42'))
    
    def testDeleteAndReadd(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('oai_dc','schema', 'namespace')])
        self.jazz.delete('42')
        self.assertTrue(self.jazz.isDeleted('42'))
        self.jazz.addOaiRecord('42', metadataFormats=[('oai_dc','schema', 'namespace')])
        self.assertFalse(self.jazz.isDeleted('42'))

        self.assertEquals(['42'], list(self.jazz.oaiSelect(prefix='oai_dc')))

    # What happens if you do addOaiRecord('id1', prefix='aap') and afterwards
    #   addOaiRecord('id1', prefix='noot')
    # According to the specification:
    # Deleted status is a property of individual records. Like a normal record, a deleted record is identified by a unique identifier, a metadataPrefix and a datestamp. Other records, with different metadataPrefix but the same unique identifier, may remain available for the item.

    def testDeleteIsPersistent(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('oai_dc','schema', 'namespace')])
        self.jazz.delete('42')
        jazz2 = OaiJazzFile(self.tempdir)
        self.assertTrue(jazz2.isDeleted('42'))

    def testAddOaiRecordPersistent(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('prefix','schema', 'namespace')], sets=[('setSpec', 'setName')])
        jazz2 = OaiJazzFile(self.tempdir)
        self.assertEquals(['42'], list(jazz2.oaiSelect(prefix='prefix', sets=['setSpec'])))

    def testWeirdSetOrPrefixNamesDoNotMatter(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('/%^!@#$   \n\t','schema', 'namespace')], sets=[('set%2Spec\n\n', 'setName')])
        jazz2 = OaiJazzFile(self.tempdir)
        self.assertEquals(['42'], list(jazz2.oaiSelect(prefix='/%^!@#$   \n\t', sets=['set%2Spec\n\n'])))
        

    def _setTime(self, year, month, day):
        self.jazz._stamp = lambda: int(mktime((year, month, day, 0, 1, 0, 0, 0 ,0))*1000000.0)
        
    def testListRecordsWithFromAndUntil(self):
        self._setTime(2007, 9, 21)
        self.jazz.addOaiRecord('4', metadataFormats=[('prefix','schema', 'namespace')])
        self._setTime(2007, 9, 22)
        self.jazz.addOaiRecord('3', metadataFormats=[('prefix','schema', 'namespace')])
        self._setTime(2007, 9, 23)
        self.jazz.addOaiRecord('2', metadataFormats=[('prefix','schema', 'namespace')])
        self._setTime(2007, 9, 24)
        self.jazz.addOaiRecord('1', metadataFormats=[('prefix','schema', 'namespace')])

        result = self.jazz.oaiSelect(prefix='prefix', oaiFrom="2007-09-22T00:00:00Z")
        self.assertEquals(3, len(list(result)))
        result = self.jazz.oaiSelect(prefix='prefix', oaiFrom="2007-09-22T00:00:00Z", oaiUntil="2007-09-23T23:59:59Z")
        self.assertEquals(2, len(list(result)))
        
    # unique, for continueAt

    def testDeleteIncrementsDatestampAndUnique(self):
        self.jazz.addOaiRecord('23', metadataFormats=[('oai_dc','schema', 'namespace')])
        stamp = self.jazz.getDatestamp('23')
        #unique = jazz.getUnique('23')
        self.stampNumber += 1234567890 # increaseTime
        self.jazz.delete('23')
        self.assertNotEqual(stamp, self.jazz.getDatestamp('23'))
        #self.assertNotEquals(unique, int(jazz.getUnique('23')))

    def testHierarchicalSets(self):
        self.jazz.addOaiRecord('record123', metadataFormats=[('oai_dc', 'schema', 'namespace')], sets=[('set1:set2:set3', 'setName123')])
        self.jazz.addOaiRecord('record124', metadataFormats=[('oai_dc', 'schema', 'namespace')], sets=[('set1:set2:set4', 'setName124')])
        
        self.assertEquals(['record123', 'record124'], list(self.jazz.oaiSelect(prefix='oai_dc', sets=['set1'])))
        self.assertEquals(['record123', 'record124'], list(self.jazz.oaiSelect(prefix='oai_dc', sets=['set1:set2'])))
        self.assertEquals(['record123'], list(self.jazz.oaiSelect(prefix='oai_dc', sets=['set1:set2:set3'])))

    def testFlattenSetHierarchy(self):
        self.assertEquals(['set1', 'set1:set2', 'set1:set2:set3'], sorted(_flattenSetHierarchy(['set1:set2:set3'])))
        self.assertEquals(['set1', 'set1:set2', 'set1:set2:set3', 'set1:set2:set4'], sorted(_flattenSetHierarchy(['set1:set2:set3', 'set1:set2:set4'])))

    def testGetUnique(self):
        newStamp = self.stampNumber
        self.jazz.addOaiRecord('id', metadataFormats=[('prefix', 'schema', 'namespace')])
        self.assertEquals(newStamp, self.jazz.getUnique('id'))

    def testOaiListWithListIdentifiers(self):
        for i in xrange(300):
            self.jazz.addOaiRecord('id:%i' % i, metadataFormats=[('prefix', 'schema', 'namespace')])
        output = StringIO()
        oaiList = OaiList()
        oaiList.addObserver(self.jazz)
        host = CallTrace('Host')
        host.port = 12345
        webrequest = CallTrace('WebRequest')
        webrequest.write = output.write
        webrequest.args = {'verb': ['ListIdentifiers'], 'metadataPrefix': ['prefix']}
        webrequest.path = '/oai'
        webrequest.returnValues['getRequestHostname'] = 'www.example.org'
        webrequest.returnValues['getHost'] = host
        oaiList.listIdentifiers(webrequest)
        output.seek(0)
        lxmlNode = parse(output)
        recordIds = lxmlNode.xpath('//oai:identifier/text()', namespaces = {'oai':"http://www.openarchives.org/OAI/2.0/"})
        self.assertEquals(['id:%d' % i for i in range(BATCH_SIZE)], recordIds)
        resumptionToken = ''.join(lxmlNode.xpath('//oai:resumptionToken/text()', namespaces = {'oai':"http://www.openarchives.org/OAI/2.0/"}))

        # now use resumptiontoken
        output = StringIO()
        webrequest.write = output.write
        webrequest.args = {'verb': ['ListIdentifiers'], 'resumptionToken':[resumptionToken]}
        oaiList.listIdentifiers(webrequest)
        output.seek(0)
        lxmlNode = parse(output)
        recordIds = lxmlNode.xpath('//oai:identifier/text()', namespaces = {'oai':"http://www.openarchives.org/OAI/2.0/"})
        self.assertEquals(['id:%d' % i for i in range(BATCH_SIZE, 300)], recordIds)

    def testOaiSelectWithContinuAt(self):
        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix', 'schema', 'namespace')])
        self.jazz.addOaiRecord('id:2', metadataFormats=[('prefix', 'schema', 'namespace')])

        continueAt = str(self.jazz.getUnique('id:1'))
        self.assertEquals(['id:2'], list(self.jazz.oaiSelect(prefix='prefix', continueAt=continueAt)))

        #add again will change the unique value
        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix', 'schema', 'namespace')])
        self.assertEquals(['id:2', 'id:1'], list(self.jazz.oaiSelect(prefix='prefix', continueAt=continueAt)))
        
    def testGetAllMetadataFormats(self):
        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix', 'schema', 'namespace')])
        self.assertEquals([('prefix', 'schema', 'namespace')], list(self.jazz.getAllMetadataFormats()))
        self.jazz.addOaiRecord('id:2', metadataFormats=[('prefix2', 'schema2', 'namespace2')])
        self.assertEquals(set([('prefix', 'schema', 'namespace'), ('prefix2', 'schema2', 'namespace2')]), set(self.jazz.getAllMetadataFormats()))

    def testGetAndAllPrefixes(self):
        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix1', 'schema', 'namespace')])
        self.jazz.addOaiRecord('id:2', metadataFormats=[('prefix1', 'schema', 'namespace'), ('prefix2', 'schema', 'namespace')])
        self.assertEquals(set(['prefix1', 'prefix2']), set(self.jazz.getAllPrefixes()))
        self.assertEquals(set(['prefix1']), set(self.jazz.getPrefixes('id:1')))
        self.assertEquals(set(['prefix1', 'prefix2']) , set(self.jazz.getPrefixes('id:2')))
        self.assertEquals(set([]), set(self.jazz.getPrefixes('doesNotExist')))

    def testGetAndAllSets(self):
        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix1', 'schema', 'namespace')], sets=[('setSpec1', 'setName1')])
        self.assertEquals(set(['setSpec1']), set(self.jazz.getSets('id:1')))
        self.jazz.addOaiRecord('id:2', metadataFormats=[('prefix1', 'schema', 'namespace')], sets=[('setSpec1', 'setName1'), ('setSpec2:setSpec3', 'setName23')])
        self.assertEquals(set(['setSpec1']), set(self.jazz.getSets('id:1')))
        self.assertEquals(set(['setSpec1', 'setSpec2', 'setSpec2:setSpec3']), set(self.jazz.getSets('id:2')))
        self.assertEquals(set([]), set(self.jazz.getSets('doesNotExist')))
        self.assertEquals(set(['setSpec1', 'setSpec2', 'setSpec2:setSpec3']), set(self.jazz.getAllSets()))

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
        #parts = jazz.getPrefixes('123')
        #self.assertEquals(['oai_dc', 'lom'], parts)
        #self.assertEquals((1, ['123']), jazz.oaiSelect(prefix='lom'))
        #self.assertEquals((1, ['123']), jazz.oaiSelect(prefix='oai_dc'))

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
        #prefixes = jazz.getAllMetadataFormats()
        #self.assertEquals([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc')], list(prefixes))
        #jazz.add('457', 'dc2', bind_string('<oai_dc:dc xmlns:oai_dc="http://dc2"/>').dc)
        #prefixes = jazz.getAllMetadataFormats()
        #self.assertEquals(set([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc'), ('dc2', '', 'http://dc2')]), prefixes)

    #def testMetadataPrefixesFromRootTag(self):
        #jazz = self.realjazz
        #jazz.add('456', 'oai_dc', bind_string('<oai_dc:dc xmlns:oai_dc="http://oai_dc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
             #xsi:schemaLocation="http://oai_dc http://oai_dc/dc.xsd"/>'))
        #prefixes = jazz.getAllMetadataFormats()
        #self.assertEquals([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc')], list(prefixes))

    #def testIncompletePrefixInfo(self):
        #jazz = self.realjazz
        #jazz.add('457', 'dc2', bind_string('<oai_dc/>').oai_dc)
        #prefixes = jazz.getAllMetadataFormats()
        #self.assertEquals(set([('dc2', '', '')]), prefixes)

    #def testPreserveRicherPrefixInfo(self):
        #jazz = self.realjazz
        #jazz.add('457', 'oai_dc', bind_string('<oai_dc:dc xmlns:oai_dc="http://oai_dc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
             #xsi:schemaLocation="http://oai_dc http://oai_dc/dc.xsd"/>').dc)
        #jazz.add('457', 'oai_dc', bind_string('<oai_dc/>'))
        #prefixes = jazz.getAllMetadataFormats()
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



#from time import sleep
#class TimerForTestSupport(object):
    #def addTimer(self, time, callback):
        #callback()

        #sleep(0.01)
        #return (time,callback)
    #def removeTimer(self, token):
        #pass
