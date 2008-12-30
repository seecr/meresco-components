## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from oaitestcase import OaiTestCase

from mockoaijazz import MockOaiJazz

from meresco.framework import ObserverFunction
from merescocomponents.oai.oaigetrecord import OaiGetRecord

from cq2utils.calltrace import CallTrace

class OaiGetRecordTest(OaiTestCase):
    def getSubject(self):
        oaigetrecord = OaiGetRecord()
        oaigetrecord.addObserver(ObserverFunction(lambda: [('oai_dc', '', '')], 'getAllPrefixes'))
        return oaigetrecord


    def testGetRecordNotAvailable(self):
        self.request.args = {'verb':['GetRecord'], 'metadataPrefix': ['oai_dc'], 'identifier': ['oai:ident']}

        observer = CallTrace('RecordAnswering')
        notifications = []
        def isAvailable(id, partName):
            notifications.append((id, partName))
            return False, False
        observer.isAvailable = isAvailable
        observer.returnValues['getDatestamp'] = 'DATESTAMP_FOR_TEST'
        self.subject.addObserver(observer)

        self.observable.any.getRecord(self.request)

        self.assertEqualsWS(self.OAIPMH % """
<request identifier="oai:ident" metadataPrefix="oai_dc" verb="GetRecord">http://server:9000/path/to/oai</request>
<error code="idDoesNotExist">The value of the identifier argument is unknown or illegal in this repository.</error>""", self.stream.getvalue())
        self.assertValidString(self.stream.getvalue())

        self.assertEquals([('oai:ident', 'oai_dc')], notifications)

    def testGetRecord(self):
        self.request.args = {'verb':['GetRecord'], 'metadataPrefix': ['oai_dc'], 'identifier': ['oai:ident']}

        self.subject.addObserver(MockOaiJazz(
            isAvailableDefault=(True, False),
            isAvailableAnswer=[(None, 'oai_dc', (True,True))]))
        self.observable.any.getRecord(self.request)
        self.assertEqualsWS(self.OAIPMH % """
<request identifier="oai:ident"
 metadataPrefix="oai_dc"
 verb="GetRecord">http://server:9000/path/to/oai</request>
   <GetRecord>
   <record>
    <header>
      <identifier>oai:ident</identifier>
      <datestamp>DATESTAMP_FOR_TEST</datestamp>
    </header>
    <metadata>
      <some:recorddata xmlns:some="http://some.example.org" id="oai:ident"/>
    </metadata>
  </record>
 </GetRecord>""", self.stream.getvalue())

    def testDeletedRecord(self):
        self.request.args = {'verb':['GetRecord'], 'metadataPrefix': ['oai_dc'], 'identifier': ['oai:ident']}

        self.subject.addObserver(MockOaiJazz(
            isAvailableDefault=(True, False),
            isAvailableAnswer=[(None, "oai_dc", (True, False))],
            deleted=['oai:ident']))
        self.observable.any.getRecord(self.request)
        self.assertTrue("deleted" in self.stream.getvalue(), self.stream.getvalue())
