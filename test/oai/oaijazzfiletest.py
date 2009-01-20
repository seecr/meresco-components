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
from merescocomponents.oai.oaijazzfile import _flattenSetHierarchy
from StringIO import StringIO
from lxml.etree import parse

from os import listdir

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
        stamps = []
        for i in xrange(1000):
            stamps.append(jazz._stamp())
            var = 30.0/2.0
        self.assertEquals(list(sorted(set(stamps))), stamps)
        
    def testResultsStored(self):
        self.jazz.addOaiRecord(identifier='oai://1234?34', sets=[], metadataFormats=[('prefix', 'schema', 'namespace')])
        self.jazz.commit()
        myJazz = OaiJazzFile(self.tempdir)
        recordIds = myJazz.oaiSelect(prefix='prefix')
        self.assertEquals('oai://1234?34', recordIds.next())

    def xtestPerformanceTestje(self):
        """This test is fast if storing on disk is off"""
        originalStore = self.jazz._store
        self.jazz._store = lambda iets:None
        t0 = time()
        for i in xrange(1 * 10**7):
            self.jazz.addOaiRecord('id%s' % i, sets=[('setSpec%s' % ((i / 100)*100), 'setName')], metadataFormats=[('prefix','schema', 'namespace')])
        t1 = time()
        ids = self.jazz.oaiSelect(sets=['setSpec95000'],prefix='prefix')
        firstId = ids.next()
        t2 = time()
        self.assertEquals(99, len(list(ids)))
        t3 = time()
        originalStore()
        t4 = time()
        jazz = OaiJazzFile(self.tempdir)
        t5 = time()
        print t1 - t0, t2 - t1, t3 -t2, t3 -t1, t4 - t3, t5 - t4
        # a set form 10 million records costs 3.9 seconds (Without any efficiency things applied
        # it costs 0.3 seconds with 1 million records
        # retimed it at 2009-01-13:
        #  1 * 10**6 oaiSelect took 3.7 seconds
        #  1 * 10**7 oaiSelect took 37.3 seconds
        # after adding low, high for sets: although this quite optimal for this test!!
        #  1 * 10**6 oaiSelect took 0.071
        #  1 * 10**7 oaiSelect took 0.071
        # the above optimization is removed again, it was only there to show optimization could help  A LOT!
        # New optimization with And, Or Iterator
        #  1 * 10**6 oaiSelect took 0.363089084625
        #  1 * 10**7 oaiSelect took 0.347623825073
        
    def testGetDatestamp(self):
        self.jazz.addOaiRecord('123', metadataFormats=[('oai_dc', 'schema', 'namespace')])
        self.assertEquals('2008-07-06T05:04:03Z', self.jazz.getDatestamp('123'))

    def testDeleteNonExistingRecords(self):
        self.jazz.addOaiRecord('existing', metadataFormats=[('prefix','schema', 'namespace')])
        self.jazz.delete('notExisting')
        self.jazz.commit()
        jazz2 = OaiJazzFile(self.tempdir)
        self.assertEquals(None, jazz2.getUnique('notExisting'))

    # What happens if you do addOaiRecord('id1', prefix='aap') and afterwards
    #   addOaiRecord('id1', prefix='noot')
    # According to the specification:
    # Deleted status is a property of individual records. Like a normal record, a deleted record is identified by a unique identifier, a metadataPrefix and a datestamp. Other records, with different metadataPrefix but the same unique identifier, may remain available for the item.

    def testDeleteIsPersistent(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('oai_dc','schema', 'namespace')])
        self.jazz.delete('42')
        self.jazz.commit()
        self.assertEquals(['42'], list(self.jazz.oaiSelect(prefix='oai_dc')))
        jazz2 = OaiJazzFile(self.tempdir)
        self.assertTrue(jazz2.isDeleted('42'))
        self.assertEquals(['42'], list(jazz2.oaiSelect(prefix='oai_dc')))

    def testAddOaiRecordPersistent(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('prefix','schema', 'namespace')], sets=[('setSpec', 'setName')])
        self.jazz.commit()
        jazz2 = OaiJazzFile(self.tempdir)
        self.assertEquals(['42'], list(jazz2.oaiSelect(prefix='prefix', sets=['setSpec'])))

    def testWeirdSetOrPrefixNamesDoNotMatter(self):
        self.jazz.addOaiRecord('42', metadataFormats=[('/%^!@#$   \n\t','schema', 'namespace')], sets=[('set%2Spec\n\n', 'setName')])
        self.jazz.commit()
        jazz2 = OaiJazzFile(self.tempdir)
        self.assertEquals(['42'], list(jazz2.oaiSelect(prefix='/%^!@#$   \n\t', sets=['set%2Spec\n\n'])))
        

        
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


