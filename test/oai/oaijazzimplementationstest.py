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

from cq2utils import CQ2TestCase, CallTrace
from merescocomponents.facetindex import LuceneIndex
from os.path import join
from merescocore.components import StorageComponent
from amara.binderytools import bind_string
from time import sleep, mktime
from StringIO import StringIO
from lxml.etree import parse
from merescocomponents.oai.oailist import OaiList

from merescocomponents.oai import OaiJazz, OaiAddRecord

class OaiJazzImplementationsTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.jazz = OaiJazz(self.tempdir)
        self.oaiAddRecord = OaiAddRecord()
        self.oaiAddRecord.addObserver(self.jazz)

    def addDocuments(self, size):
        for id in range(1,size+1):
            self._addRecord(id)

    def _addRecord(self, anId):
        self.jazz.addOaiRecord('%05d' % anId, metadataFormats=[('oai_dc', 'dc.xsd', 'oai_dc.example.org')])

    def testAddDocument(self):
        self.addDocuments(1)
        result = self.jazz.oaiSelect(prefix='oai_dc')
        self.assertEquals(['00001'], list(result))

    def testListRecords(self):
        #BooleanQuery.setMaxClauseCount(10) # Cause an early TooManyClauses exception.
        self.addDocuments(50)
        result = self.jazz.oaiSelect(prefix='oai_dc')
        self.assertEquals('00001', result.next())
        result = self.jazz.oaiSelect(prefix='oai_dc', continueAfter=str(self.jazz.getUnique('00001')))
        self.assertEquals('00002', result.next())

    def testAddOaiRecordWithNoMetadataFormats(self):
        try:
            self.jazz.addOaiRecord('identifier', sets=[('setSpec', 'setName')], metadataFormats=[])
            self.fail()
        except Exception, e:
            self.assertTrue('metadataFormat' in str(e))

    def testGetFromMultipleSets(self):
        self.jazz.addOaiRecord('id1', sets=[('set1', 'set1name')], metadataFormats=[('prefix','schema', 'namespace')])
        self.jazz.addOaiRecord('id2', sets=[('set2', 'set2name')], metadataFormats=[('prefix','schema', 'namespace')])
        self.jazz.addOaiRecord('id3', sets=[('set3', 'set1name')], metadataFormats=[('prefix','schema', 'namespace')])
        self.assertEquals(['id1','id2'], list(self.jazz.oaiSelect(sets=['set1','set2'], prefix='prefix')))

    def testDeleteIncrementsDatestampAndUnique(self):
        header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>%s</setSpec></header>'
        self.oaiAddRecord.add('23', 'oai_dc', bind_string(header % 'aSet').header)
        stamp = self.jazz.getDatestamp('23')
        unique = self.jazz.getUnique('23')
        sleep(1)
        self.jazz.delete('23')
        self.assertNotEqual(stamp,  self.jazz.getDatestamp('23'))
        self.assertTrue(int(self.jazz.getUnique('23')) > int(unique))

    def testListRecordsNoResults(self):
        result = self.jazz.oaiSelect(prefix='xxx')
        self.assertEquals([], list(result))
    
    def testAddSetInfo(self):
        header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>%s</setSpec></header>'
        self.oaiAddRecord.add('123', 'oai_dc', bind_string(header % 1).header)
        self.oaiAddRecord.add('124', 'oai_dc', bind_string(header % 2).header)
        results = self.jazz.oaiSelect(sets=['1'], prefix='oai_dc')
        self.assertEquals(1, len(list(results)))
        results = self.jazz.oaiSelect(sets=['2'], prefix='oai_dc')
        self.assertEquals(1, len(list(results)))
        results = self.jazz.oaiSelect(prefix='oai_dc')
        self.assertEquals(2, len(list(results)))

    def testGetAndAllSets(self):
        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix1', 'schema', 'namespace')], sets=[('setSpec1', 'setName1')])
        self.assertEquals(set(['setSpec1']), set(self.jazz.getSets('id:1')))
        self.jazz.addOaiRecord('id:2', metadataFormats=[('prefix1', 'schema', 'namespace')], sets=[('setSpec1', 'setName1'), ('setSpec2:setSpec3', 'setName23')])
        self.assertEquals(set(['setSpec1']), set(self.jazz.getSets('id:1')))
        self.assertEquals(set(['setSpec1', 'setSpec2', 'setSpec2:setSpec3']), set(self.jazz.getSets('id:2')))
        self.assertEquals(set([]), set(self.jazz.getSets('doesNotExist')))
        self.assertEquals(set(['setSpec1', 'setSpec2', 'setSpec2:setSpec3']), set(self.jazz.getAllSets()))

    def testHierarchicalSets(self):
        self.jazz.addOaiRecord('record123', metadataFormats=[('oai_dc', 'schema', 'namespace')], sets=[('set1:set2:set3', 'setName123')])
        self.jazz.addOaiRecord('record124', metadataFormats=[('oai_dc', 'schema', 'namespace')], sets=[('set1:set2:set4', 'setName124')])
        
        self.assertEquals(['record123', 'record124'], list(self.jazz.oaiSelect(prefix='oai_dc', sets=['set1'])))
        self.assertEquals(['record123', 'record124'], list(self.jazz.oaiSelect(prefix='oai_dc', sets=['set1:set2'])))
        self.assertEquals(['record123'], list(self.jazz.oaiSelect(prefix='oai_dc', sets=['set1:set2:set3'])))

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
        self.assertEquals(['id:1'], list(result))

    def testAddPartWithUniqueNumbersAndSorting(self):
        self.oaiAddRecord.add('123', 'oai_dc', bind_string('<oai_dc/>'))
        self.oaiAddRecord.add('124', 'lom', bind_string('<lom/>'))
        self.oaiAddRecord.add('121', 'lom', bind_string('<lom/>'))
        self.oaiAddRecord.add('122', 'lom', bind_string('<lom/>'))
        results = self.jazz.oaiSelect(prefix='oai_dc')
        self.assertEquals(1, len(list(results)))
        results = self.jazz.oaiSelect(prefix='lom')
        self.assertEquals(['124', '121','122'], list(results))
    
    def testAddOaiRecordWithUniqueNumbersAndSorting(self):
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

    def testDelete(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('oai_dc','schema', 'namespace')])
        self.assertFalse(self.jazz.isDeleted('42'))
        self.assertEquals(['42'], list(self.jazz.oaiSelect(prefix='oai_dc')))
        self.jazz.delete('42')
        self.assertTrue(self.jazz.isDeleted('42'))
        self.assertEquals(['42'], list(self.jazz.oaiSelect(prefix='oai_dc')))

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

    def testOaiSelectWithContinuAt(self):
        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix', 'schema', 'namespace')])
        self.jazz.addOaiRecord('id:2', metadataFormats=[('prefix', 'schema', 'namespace')])
        
        continueAfter = str(self.jazz.getUnique('id:1'))
        self.assertEquals(['id:2'], list(self.jazz.oaiSelect(prefix='prefix', continueAfter=continueAfter)))

        #add again will change the unique value
        self.jazz.addOaiRecord('id:1', metadataFormats=[('prefix', 'schema', 'namespace')])
        self.assertEquals(['id:2', 'id:1'], list(self.jazz.oaiSelect(prefix='prefix', continueAfter=continueAfter)))
        
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

    def testOaiListWithListIdentifiers(self):
        BATCH_SIZE = 10
        for i in xrange(BATCH_SIZE + 5):
            self.jazz.addOaiRecord('id:%i' % i, metadataFormats=[('prefix', 'schema', 'namespace')])
        output = StringIO()
        oaiList = OaiList(batchSize=BATCH_SIZE)
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
        self.assertEquals(['id:%d' % i for i in range(BATCH_SIZE, BATCH_SIZE +5)], recordIds)

    def testPreserveRicherPrefixInfo(self):
        self.oaiAddRecord.add('457', 'oai_dc', bind_string('<oai_dc:dc xmlns:oai_dc="http://oai_dc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
             xsi:schemaLocation="http://oai_dc http://oai_dc/dc.xsd"/>').dc)
        self.oaiAddRecord.add('457', 'oai_dc', bind_string('<oai_dc/>'))
        metadataFormats = set(self.jazz.getAllMetadataFormats())
        self.assertEquals(set([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc')]), metadataFormats)

    def testIncompletePrefixInfo(self):
        self.oaiAddRecord.add('457', 'dc2', bind_string('<oai_dc/>').oai_dc)
        metadataFormats = set(self.jazz.getAllMetadataFormats())
        self.assertEquals(set([('dc2', '', '')]), metadataFormats)

    def testMetadataPrefixesOnly(self):
        self.oaiAddRecord.add('456', 'oai_dc', bind_string('<oai_dc:dc xmlns:oai_dc="http://oai_dc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
             xsi:schemaLocation="http://oai_dc http://oai_dc/dc.xsd"/>').dc)
        prefixes = set(self.jazz.getAllPrefixes())
        self.assertEquals(set(['oai_dc']), prefixes)
        self.oaiAddRecord.add('457', 'dc2', bind_string('<oai_dc:dc xmlns:oai_dc="http://dc2"/>').dc)
        prefixes = set(self.jazz.getAllPrefixes())
        self.assertEquals(set(['oai_dc', 'dc2']), prefixes)
        
    def testGetPrefixes(self):
        self.oaiAddRecord.add('123', 'oai_dc', bind_string('<dc/>').dc)
        self.oaiAddRecord.add('123', 'lom', bind_string('<lom/>').lom)
        parts = set(self.jazz.getPrefixes('123'))
        self.assertEquals(set(['oai_dc', 'lom']), parts)
        self.assertEquals(['123'], list(self.jazz.oaiSelect(prefix='lom')))
        self.assertEquals(['123'], list(self.jazz.oaiSelect(prefix='oai_dc')))

    def _setTime(self, year, month, day):
        self.jazz._stamp = lambda: int(mktime((year, month, day, 0, 1, 0, 0, 0 ,0))*1000000.0)
