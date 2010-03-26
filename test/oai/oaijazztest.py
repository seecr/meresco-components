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
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
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
from time import time, mktime, strptime, sleep

from merescocomponents.oai import OaiJazz
from merescocomponents.oai.oaijazz import _flattenSetHierarchy, RecordId, SETSPEC_SEPARATOR
from StringIO import StringIO
from lxml.etree import parse
from merescocore.framework import Observable, be, Transparant

from os import listdir
from shutil import rmtree

class OaiJazzTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.jazz = OaiJazz(self.tempdir)
        self.stampNumber = int(mktime((2008, 07, 06, 05, 04, 03, 0, 0, 1)))*1000000
        def stamp():
            result = self.stampNumber
            self.stampNumber += 1
            return result
        self.jazz._stamp = stamp

    def testOriginalStamp(self):
        jazz = OaiJazz(self.tempdir)
        stamp0 = jazz._stamp()
        sleep(0.0001)
        stamp1 = jazz._stamp()
        self.assertTrue(stamp0 < stamp1, "Expected %s < %s" % (stamp0, stamp1))

    def testResultsStored(self):
        self.jazz.addOaiRecord(identifier='oai://1234?34', sets=[], metadataFormats=[('prefix', 'schema', 'namespace')])
        myJazz = OaiJazz(self.tempdir)
        recordIds = myJazz.oaiSelect(prefix='prefix')
        self.assertEquals('oai://1234?34', recordIds.next())

    def xtestPerformanceTestje(self):
        t0 = time()
        lastTime = t0
        for i in xrange(1, 10**4 + 1):
            self.jazz.addOaiRecord('id%s' % i, sets=[('setSpec%s' % ((i / 100)*100), 'setName')], metadataFormats=[('prefix','schema', 'namespace')])
            if i%1000 == 0 and i > 0:
                tmp = time()
                print '%7d' % i, '%.4f' % (tmp - lastTime), '%.6f' % ((tmp - t0)/float(i))
                lastTime = tmp
        t1 = time()
        ids = self.jazz.oaiSelect(sets=['setSpec9500'],prefix='prefix')
        firstId = ids.next()
        allids = [firstId]
        t2 = time()
        allids.extend(list(ids))
        self.assertEquals(100, len(allids))
        t3 = time()
        for identifier in allids:
            list(self.jazz.getSets(identifier))
        t4 = time()
        jazz = OaiJazz(self.tempdir)
        t5 = time()
        print t1 - t0, t2 - t1, t3 -t2, t3 -t1, t4 - t3, t5 - t4
        # a set form 10 million records costs 3.9 seconds (Without any efficiency things applied
        # it costs 0.3 seconds with 1 million records
        # retimed it at 2009-01-13:
        #  1 * 10**6 oaiSelect took 3.7 seconds
        #  1 * 10**7 oaiSelect took 37.3 seconds
        # New optimization with And, Or Iterator
        #  1 * 10**6 oaiSelect took 0.363089084625
        #  1 * 10**7 oaiSelect took 0.347623825073
        # New implementation with LuceneDict and SortedFileList with delete support
        #  insert of 10*4 took 153 secs
        #  oaiSelect took 0.1285
        # 2009-11-18: new implementation of lookup of sets for an identifier (getSets) using
        # berkeleydict.
        # previous getSets(id) for 100 identifiers took 1.10 secs
        # after getSets(id) for 100 identifiers took 0.004 secs
        # penalty on insertion of 10.000 records previous 22 secs, after 27 secs
        # Same test but with 100.000 records (ulimit must be increased)
        # 285.413653135 0.240143060684 0.0137410163879 0.253884077072 0.00416588783264 0.167983055115
        # 237.773926973 0.240620851517 0.0134921073914 0.254112958908 14.3589520454 0.160785913467

    def testGetDatestamp(self):
        self.jazz.addOaiRecord('123', metadataFormats=[('oai_dc', 'schema', 'namespace')])
        self.assertEquals('2008-07-06T05:04:03Z', self.jazz.getDatestamp('123'))

    def testDeleteNonExistingRecords(self):
        self.jazz.addOaiRecord('existing', metadataFormats=[('prefix','schema', 'namespace')])
        self.jazz.delete('notExisting')
        jazz2 = OaiJazz(self.tempdir)
        self.assertEquals(None, jazz2.getUnique('notExisting'))

    def testDoNotPerformSuperfluousDeletes(self):
        self.jazz.addOaiRecord('existing', metadataFormats=[('prefix','schema', 'namespace')])
        self.jazz._stamp2identifier = CallTrace('mockdict', returnValues={'getKeysFor': None, '__delitem__':None})
        self.jazz.delete('notExisting')
        self.assertFalse("__delitem__" in str(self.jazz._stamp2identifier.calledMethods))

    # What happens if you do addOaiRecord('id1', prefix='aap') and afterwards
    #   addOaiRecord('id1', prefix='noot')
    # According to the specification:
    # Deleted status is a property of individual records. Like a normal record, a deleted record is identified by a unique identifier, a metadataPrefix and a datestamp. Other records, with different metadataPrefix but the same unique identifier, may remain available for the item.

    def testDeleteIsPersistent(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('oai_dc','schema', 'namespace')])
        self.jazz.delete('42')
        self.assertEquals(['42'], list(self.jazz.oaiSelect(prefix='oai_dc')))
        jazz2 = OaiJazz(self.tempdir)
        self.assertTrue(jazz2.isDeleted('42'))
        self.assertEquals(['42'], list(jazz2.oaiSelect(prefix='oai_dc')))

    def testAddOaiRecordPersistent(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('prefix','schema', 'namespace')], sets=[('setSpec', 'setName')])
        jazz2 = OaiJazz(self.tempdir)
        self.assertEquals(['42'], list(jazz2.oaiSelect(prefix='prefix', sets=['setSpec'])))

    def testWeirdSetOrPrefixNamesDoNotMatter(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('/%^!@#$   \n\t','schema', 'namespace')], sets=[('set%2Spec\n\n', 'setName')])
        jazz2 = OaiJazz(self.tempdir)
        self.assertEquals(['42'], list(jazz2.oaiSelect(prefix='/%^!@#$   \n\t', sets=['set%2Spec\n\n'])))


    def testOaiSelectWithFromAfterEndOfTime(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('oai_dc','schema', 'namespace')])
        result = self.jazz.oaiSelect(prefix='oai_dc', oaiFrom='9999-01-01T00:00:00Z')
        self.assertEquals(0,len(list(result)))

    # unique, for continueAfter

    def testDeleteIncrementsDatestampAndUnique(self):
        self.jazz.addOaiRecord('23', metadataFormats=[('oai_dc','schema', 'namespace')])
        stamp = self.jazz.getDatestamp('23')
        #unique = jazz.getUnique('23')
        self.stampNumber += 1234567890 # increaseTime
        self.jazz.delete('23')
        self.assertNotEqual(stamp, self.jazz.getDatestamp('23'))
        #self.assertNotEquals(unique, int(jazz.getUnique('23')))

    def testFlattenSetHierarchy(self):
        self.assertEquals(['set1', 'set1:set2', 'set1:set2:set3'], sorted(_flattenSetHierarchy(['set1:set2:set3'])))
        self.assertEquals(['set1', 'set1:set2', 'set1:set2:set3', 'set1:set2:set4'], sorted(_flattenSetHierarchy(['set1:set2:set3', 'set1:set2:set4'])))

    def testGetUnique(self):
        newStamp = self.stampNumber
        self.jazz.addOaiRecord('id', metadataFormats=[('prefix', 'schema', 'namespace')])
        self.assertEquals(newStamp, self.jazz.getUnique('id'))

    def testWithObservablesAndUseOfAnyBreaksStuff(self):
        self.jazz.addOaiRecord('23', metadataFormats=[('one','schema1', 'namespace1'), ('two','schema2', 'namespace2')])
        server = be((Observable(),
            (Transparant(),
                (self.jazz,)
            )
        ))
        server.once.observer_init()
        mf = list(server.any.getAllMetadataFormats())
        self.assertEquals(2, len(mf))
        self.assertEquals(set(['one', 'two']), set(prefix for prefix, schema, namespace in mf))

    def testRecordId(self):
        r = RecordId('identifier', 12345)
        self.assertEquals(12345, r.stamp)
        self.assertEquals('identifier', r)
        r2 = r[6:]
        self.assertEquals('fier', r2)
        self.assertEquals(12345, r2.stamp)
        
    def testGetNrOfRecords(self):
        self.assertEquals(0, self.jazz.getNrOfRecords('aPrefix'))        
        self.jazz.addOaiRecord('id1', metadataFormats=[('aPrefix', 'schema', 'namespace')])
        self.assertEquals(1, self.jazz.getNrOfRecords('aPrefix'))
        self.assertEquals(0, self.jazz.getNrOfRecords('anotherPrefix'))        
        self.jazz.addOaiRecord('id2', metadataFormats=[('aPrefix', 'schema', 'namespace')])
        self.assertEquals(2, self.jazz.getNrOfRecords('aPrefix'))
        self.jazz.delete('id1')
        self.assertEquals(2, self.jazz.getNrOfRecords('aPrefix'))
        
    def testIllegalSetRaisesException(self):
        # XSD: http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd
        # according to the xsd the setSpec should conform to:
        # ([A-Za-z0-9\-_\.!~\*'\(\)])+(:[A-Za-z0-9\-_\.!~\*'\(\)]+)*
        #
        # we will only check that a , (comma) is not used.
        self.assertEquals(',', SETSPEC_SEPARATOR)
        self.assertRaises(AssertionError, lambda: self.jazz.addOaiRecord('42', metadataFormats=[('prefix','schema', 'namespace')], sets=[('setSpec,', 'setName')]))
        
    def testConversionNeeded(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('prefix','schema', 'namespace')], sets=[('setSpec', 'setName')])
        rmtree(join(self.tempdir, 'identifier2setSpecs'))
        self.assertRaises(AssertionError, lambda: OaiJazz(self.tempdir))
        
