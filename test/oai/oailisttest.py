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

from StringIO import StringIO

from amara.binderytools import bind_string
from cq2utils.calltrace import CallTrace

from mockoaijazz import MockOaiJazz

from meresco.framework import ObserverFunction
from merescocomponents.oai.oailist import BATCH_SIZE, OaiList
from merescocomponents.oai.resumptiontoken import resumptionTokenFromString, ResumptionToken

from oaitestcase import OaiTestCase

class OaiListTest(OaiTestCase):
    def getSubject(self):
        oailist = OaiList()
        oailist.addObserver(ObserverFunction(lambda: [('oai_dc', '', '')], 'getAllPrefixes'))
        return oailist


    def testListRecordsUsingMetadataPrefix(self):
        self.request.args = {'verb':['ListRecords'], 'metadataPrefix': ['oai_dc']}

        mockoaijazz = MockOaiJazz(
            selectAnswer=['id_0&0', 'id_1&1'],
            selectTotal=2,
            isAvailableDefault=(True,True),
            isAvailableAnswer=[
                (None, 'oai_dc', (True,False)),
                (None, '__tombstone__', (True, False))])
        self.subject.addObserver(mockoaijazz)
        
        self.observable.any.listRecords(self.request)

        self.assertEqualsWS(self.OAIPMH % """
<request metadataPrefix="oai_dc"
 verb="ListRecords">http://server:9000/path/to/oai</request>
 <ListRecords>
   <record>
    <header>
      <identifier>id_0&amp;0</identifier>
      <datestamp>DATESTAMP_FOR_TEST</datestamp>
    </header>
    <metadata>
      <some:recorddata xmlns:some="http://some.example.org" id="id_0&amp;0"/>
    </metadata>
   </record>
   <record>
    <header>
      <identifier>id_1&amp;1</identifier>
      <datestamp>DATESTAMP_FOR_TEST</datestamp>
    </header>
    <metadata>
      <some:recorddata xmlns:some="http://some.example.org" id="id_1&amp;1"/>
    </metadata>
   </record>
 </ListRecords>""" , self.stream.getvalue())
        self.assertTrue(self.stream.getvalue().find('<resumptionToken') == -1)
        self.assertFalse(mockoaijazz.oaiSelectArguments[0])
        

    def testListRecordsWithoutProvenance(self):
        self.request.args = {'verb':['ListRecords'], 'metadataPrefix': ['oai_dc']}

        self.subject.addObserver(MockOaiJazz(
            selectAnswer=['id_0&0', 'id_1&1'],
            isAvailableDefault=(True,True),
            isAvailableAnswer=[
                (None, 'oai_dc', (True,False)),
                (None, '__tombstone__', (True, False))]))

        self.observable.any.listRecords(self.request)
        self.assertFalse('<about' in self.stream.getvalue())

    def testListRecordsWithProvenance(self):
        class MockOaiProvenance(object):
            def provenance(inner, id):
                yield "PROVENANCE"

        self.request.args = {'verb':['ListRecords'], 'metadataPrefix': ['oai_dc']}

        self.subject.addObserver(MockOaiProvenance())
        self.subject.addObserver(MockOaiJazz(
            selectAnswer=['id_0&0', 'id_1&1'],
            isAvailableDefault=(True,True),
            isAvailableAnswer=[
                (None, 'oai_dc', (True,False)),
                (None, '__tombstone__', (True, False))]))

        self.observable.any.listRecords(self.request)
        result = self.stream.getvalue()
        self.assertTrue('<about>PROVENANCE</about>' in result, result)

    def testListRecordsUsingToken(self):
        self.request.args = {'verb':['ListRecords'], 'resumptionToken': [str(ResumptionToken('oai_dc', '10', 'FROM', 'UNTIL', 'SET'))]}

        observer = CallTrace('RecordAnswering')
        def oaiSelect(sets, prefix, continueAt, oaiFrom, oaiUntil, batchSize):
            self.assertEquals('SET', sets[0])
            self.assertEquals('oai_dc', prefix)
            self.assertEquals('10', continueAt)
            self.assertEquals('FROM', oaiFrom)
            self.assertEquals('UNTIL', oaiUntil)
            self.assertEquals(BATCH_SIZE, batchSize)
            return 0, []

        observer.oaiSelect = oaiSelect
        self.subject.addObserver(observer)
        result = self.observable.any.listRecords(self.request)


    def testResumptionTokensAreProduced(self):
        self.request.args = {'verb':['ListRecords'], 'metadataPrefix': ['oai_dc'], 'from': ['2000-01-01T00:00:00Z'], 'until': ['2000-12-31T00:00:00Z'], 'set': ['SET']}
        observer = CallTrace('RecordAnswering')
        def oaiSelect(sets, prefix, continueAt, oaiFrom, oaiUntil, batchSize):
            return 1000, map(lambda i: 'id_%i' % i, range(batchSize))
        def writeRecord(*args, **kwargs):
            pass
        observer.oaiSelect = oaiSelect
        observer.getUnique = lambda x: 'UNIQUE_FOR_TEST'
        self.subject.addObserver(observer)
        self.subject.writeRecord = writeRecord

        self.observable.any.listRecords(self.request)

        self.assertTrue(self.stream.getvalue().find("<resumptionToken>") > -1)
        xml = bind_string(self.stream.getvalue()).OAI_PMH.ListRecords.resumptionToken
        resumptionToken = resumptionTokenFromString(str(xml))
        self.assertEquals('UNIQUE_FOR_TEST', resumptionToken._continueAt)
        self.assertEquals('oai_dc', resumptionToken._metadataPrefix)
        self.assertEquals('2000-01-01T00:00:00Z', resumptionToken._from)
        self.assertEquals('2000-12-31T00:00:00Z', resumptionToken._until)
        self.assertEquals('SET', resumptionToken._set)

    def testFinalResumptionToken(self):
        self.request.args = {'verb':['ListRecords'], 'resumptionToken': [str(ResumptionToken('oai_dc', '200'))]}

        self.subject.addObserver(MockOaiJazz(selectAnswer=map(lambda i: 'id_%i' % i, range(BATCH_SIZE)), selectTotal = BATCH_SIZE))
        self.subject.writeRecord = lambda *args, **kwargs: None

        self.observable.any.listRecords(self.request)

        self.assertTrue(self.stream.getvalue().find("<resumptionToken") > -1)
        self.assertEquals('', str(bind_string(self.stream.getvalue()).OAI_PMH.ListRecords.resumptionToken))

    def testDeletedTombstones(self):
        self.request.args = {'verb':['ListRecords'], 'metadataPrefix': ['oai_dc']}

        self.subject.addObserver(MockOaiJazz(
            selectAnswer=['id_0', 'id_1'],
            deleted=['id_1'],
            isAvailableDefault=(True,False),
            selectTotal = 2))

        self.observable.any.listRecords(self.request)

        self.assertEqualsWS(self.OAIPMH % """
<request metadataPrefix="oai_dc"
 verb="ListRecords">http://server:9000/path/to/oai</request>
 <ListRecords>
   <record>
    <header>
      <identifier>id_0</identifier>
      <datestamp>DATESTAMP_FOR_TEST</datestamp>
    </header>
    <metadata>
      <some:recorddata xmlns:some="http://some.example.org" id="id_0"/>
    </metadata>
   </record>
   <record>
    <header status="deleted">
      <identifier>id_1</identifier>
      <datestamp>DATESTAMP_FOR_TEST</datestamp>
    </header>
   </record>
 </ListRecords>""", self.stream.getvalue())

        self.assertTrue(self.stream.getvalue().find('<resumptionToken') == -1)

    def testFromAndUntil(self):
        #ok, deze test wordt zo lang dat het haast wel lijkt of hier iets niet klopt.... KVS

        observer = MockOaiJazz(
            selectAnswer=['id_0', 'id_1'],
            isAvailableDefault=(True, False),
            isAvailableAnswer=[("id_1", "__tombstone__", (True, True))])

        self.subject.addObserver(observer)

        def doIt(oaiFrom, oaiUntil):
            self.stream = StringIO()
            self.request.write = self.stream.write
            self.request.args = {'verb':['ListRecords'], 'metadataPrefix': ['oai_dc']}
            if oaiFrom:
                self.request.args['from'] = [oaiFrom]
            if oaiUntil:
                self.request.args['until'] = [oaiUntil]
            self.observable.any.listRecords(self.request)
            return [observer.oaiSelectArguments[3], observer.oaiSelectArguments[4]]

        def right(oaiFrom, oaiUntil, expectedFrom = None, expectedUntil = None):
            expectedFrom = expectedFrom or oaiFrom
            expectedUntil = expectedUntil or oaiUntil
            resultingOaiFrom, resultingOaiUntil = doIt(oaiFrom, oaiUntil)
            self.assertEquals(expectedFrom, resultingOaiFrom)
            self.assertEquals(expectedUntil, resultingOaiUntil)
            self.assertTrue(not "<error" in self.stream.getvalue(), self.stream.getvalue())

        def wrong(oaiFrom, oaiUntil):
            doIt(oaiFrom, oaiUntil)
            self.assertTrue("""<error code="badArgument">""" in self.stream.getvalue())

        #start reading here
        right(None, None)
        right('2000-01-01T00:00:00Z', '2000-01-01T00:00:00Z')
        right('2000-01-01', '2000-01-01', '2000-01-01T00:00:00Z', '2000-01-01T23:59:59Z')
        right(None, '2000-01-01T00:00:00Z')
        right('2000-01-01T00:00:00Z', None)
        wrong('thisIsNotEvenADateStamp', 'thisIsNotEvenADateStamp')
        wrong('2000-01-01T00:00:00Z', '2000-01-01')
        wrong('2000-01-01T00:00:00Z', '1999-01-01T00:00:00Z')

    def testListIdentifiers(self):
        self.request.args = {'verb':['ListIdentifiers'], 'metadataPrefix': ['oai_dc']}

        self.subject.addObserver(MockOaiJazz(
            selectAnswer=['id_0'],
            isAvailableDefault=(True,False),
            isAvailableAnswer=[(None, 'oai_dc', (True,True))],
            selectTotal=1))
        self.observable.any.listIdentifiers(self.request)

        self.assertEqualsWS(self.OAIPMH % """
<request metadataPrefix="oai_dc"
 verb="ListIdentifiers">http://server:9000/path/to/oai</request>
 <ListIdentifiers>
    <header>
      <identifier>id_0</identifier>
      <datestamp>DATESTAMP_FOR_TEST</datestamp>
    </header>
 </ListIdentifiers>""", self.stream.getvalue())

    def testNoRecordsMatch(self):
        self.request.args = {'verb':['ListIdentifiers'], 'metadataPrefix': ['oai_dc']}

        self.subject.addObserver(MockOaiJazz(selectTotal = 0))
        self.observable.any.listIdentifiers(self.request)

        self.assertTrue(self.stream.getvalue().find("noRecordsMatch") > -1)

    def testSetsInHeader(self):
        self.request.args = {'verb':['ListRecords'], 'metadataPrefix': ['oai_dc']}

        self.subject.addObserver(MockOaiJazz(
            selectAnswer=['id_0&0', 'id_1&1'],
            setsAnswer=['one:two:three', 'one:two:four'],
            isAvailableDefault=(True,False),
            isAvailableAnswer=[
                (None, 'oai_dc', (True, True)),
                (None, '__sets__', (True, True))]))
        self.observable.any.listRecords(self.request)

        self.assertTrue("<setSpec>one:two:three</setSpec>" in self.stream.getvalue())
        self.assertTrue("<setSpec>one:two:four</setSpec>" in self.stream.getvalue())

