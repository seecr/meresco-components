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
from unittest import TestCase
from time import strftime, gmtime, sleep
from cq2utils import CQ2TestCase, CallTrace

from os.path import join
from PyLucene import BooleanQuery
from storage import Storage
from amara import binderytools
from amara.binderytools import bind_string

from merescocomponents.oai import OaiJazzLucene, OaiAddRecord
from merescocomponents.oai.xml2document import TEDDY_NS, Xml2Document
from merescocore.framework.observable import Observable
from merescocomponents.facetindex import Document, LuceneIndex
from merescocore.components import StorageComponent

FIELDS = binderytools.bind_string("""<xmlfields xmlns:teddy="%s">
    <field1>this is field1</field1>
    <untokenizedField teddy:tokenize="false">this should not be tokenized</untokenizedField>
</xmlfields>""" % TEDDY_NS).xmlfields

class OaiJazzLuceneTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.index = CallTrace("Index")
        self.storage = CallTrace("Storage")
        self.mockedjazz = OaiJazzLucene(self.index, self.storage, (i for i in xrange(100)))
        self.id = "id"
        self.partName = "xmlfields"
        self.document = Xml2Document()._create(self.id, FIELDS)
        self.realjazz = OaiJazzLucene(
            LuceneIndex(
                join(self.tempdir,'index'), timer=TimerForTestSupport()),
            StorageComponent(join(self.tempdir,'storage')),
            iter(xrange(99)))

        self.oaiAddRecord = OaiAddRecord()
        self.oaiAddRecord.addObserver(self.realjazz)

    def tearDown(self):
        self.realjazz.close()
        CQ2TestCase.tearDown(self)

    def testAdd(self):
        self.index.ignoredAttributes = ['isAvailable', 'store', 'unknown', 'deletePart']
        self.mockedjazz.addOaiRecord(self.id, metadataFormats=[('partName', '', '')])

        self.assertEquals(1,len(self.index.calledMethods))
        self.assertEquals('addDocument', self.index.calledMethods[0].name)
        self.assertEquals([Document], [type(arg) for arg in self.index.calledMethods[0].args])

    def testGetUnique(self):
        self.index.ignoredAttributes=['isAvailable', 'getStream']
        def getStream(id, partName):
            yield """<oaimeta>
        <stamp>DATESTAMP_FOR_TEST</stamp>
        <unique>UNIQUE_FOR_TEST</unique>
		<sets/>
		<prefixes/>
    </oaimeta>"""
        self.storage.getStream = getStream
        self.storage.isAvailable = lambda id, part: (True, True)
        uniqueNumber = self.mockedjazz.getUnique('somedocid')
        self.assertEquals('UNIQUE_FOR_TEST', uniqueNumber)

    def testDatestamp(self):
        jazz = self.realjazz
        lower = strftime('%Y-%m-%dT%H:%M:%SZ', gmtime())
        self.oaiAddRecord.add('456', 'oai_dc', bind_string('<data/>'))
        upper = strftime('%Y-%m-%dT%H:%M:%SZ', gmtime())
        datestamp = jazz.getDatestamp('456')
        self.assertTrue(lower <= datestamp <= upper, datestamp)

    def testFixUntil(self):
        self.assertEquals("2007-09-22T12:33:00Z", self.realjazz._fixUntilDate("2007-09-22T12:33:00Z"))
        self.assertEquals("2007-09-23T00:00:00Z", self.realjazz._fixUntilDate("2007-09-22"))
        self.assertEquals("2008-01-01T00:00:00Z", self.realjazz._fixUntilDate("2007-12-31"))
        self.assertEquals("2004-02-29T00:00:00Z", self.realjazz._fixUntilDate("2004-02-28"))
        

from time import sleep
class TimerForTestSupport(object):
    def addTimer(self, time, callback):
        callback()

        sleep(0.01)
        return (time,callback)
    def removeTimer(self, token):
        pass
