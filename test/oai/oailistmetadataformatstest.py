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
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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
from os.path import join

from oaitestcase import OaiTestCase
from merescocomponents.facetindex import LuceneIndex
from meresco.components import StorageComponent
from merescocomponents.oai import OaiAddRecord, OaiJazz
from merescocomponents.oai.oailistmetadataformats import OaiListMetadataFormats
from meresco.core import be, Observable
from lxml.etree import parse
from StringIO import StringIO

from cq2utils import CallTrace

parseLxml = lambda s: parse(StringIO(s)).getroot()

class OaiListMetadataFormatsTest(OaiTestCase):

    def getSubject(self):
        return OaiListMetadataFormats()

    def testListAllMetadataFormats(self):
        class MockJazz:
            def getAllMetadataFormats(*args):
                return [
                    ('oai_dc', 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd', 'http://www.openarchives.org/OAI/2.0/oai_dc/'),
                    ('olac', 'http://www.language-archives.org/OLAC/olac-0.2.xsd','http://www.language-archives.org/OLAC/0.2/')
                ]
        self.subject.addObserver(MockJazz())
        self.request.args = {'verb': ['ListMetadataFormats']}
        self.observable.any.listMetadataFormats(self.request)
        self.assertEqualsWS(self.OAIPMH % """
        <request verb="ListMetadataFormats">http://server:9000/path/to/oai</request>
  <ListMetadataFormats>
   <metadataFormat>
     <metadataPrefix>oai_dc</metadataPrefix>
     <schema>http://www.openarchives.org/OAI/2.0/oai_dc.xsd
       </schema>
     <metadataNamespace>http://www.openarchives.org/OAI/2.0/oai_dc/
       </metadataNamespace>
   </metadataFormat>
   <metadataFormat>
     <metadataPrefix>olac</metadataPrefix>
     <schema>http://www.language-archives.org/OLAC/olac-0.2.xsd</schema>
     <metadataNamespace>http://www.language-archives.org/OLAC/0.2/
      </metadataNamespace>
   </metadataFormat>
  </ListMetadataFormats>""", self.stream.getvalue())
        self.assertValidString(self.stream.getvalue())

    def assertWithJazz(self, jazz):
        server = be((Observable(),
            (OaiAddRecord(),
                (jazz,)
            )
        ))
        self.subject.addObserver(jazz)
        self.request.args = {'verb': ['ListMetadataFormats'], 'identifier': ['id_0']}
        server.do.add('id_0', 'oai_dc', parseLxml("""<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"></oai_dc:dc>"""))
        server.do.add('id_0', 'olac', parseLxml('<tag/>'))
        self.subject.listMetadataFormats(self.request)
        self.assertEqualsWS(self.OAIPMH % """<request identifier="id_0" verb="ListMetadataFormats">http://server:9000/path/to/oai</request>
    <ListMetadataFormats>
        <metadataFormat>
            <metadataPrefix>oai_dc</metadataPrefix>
            <schema>http://www.openarchives.org/OAI/2.0/oai_dc.xsd</schema>
            <metadataNamespace>http://www.openarchives.org/OAI/2.0/oai_dc/</metadataNamespace>
        </metadataFormat>
        <metadataFormat>
            <metadataPrefix>olac</metadataPrefix>
            <schema></schema>
            <metadataNamespace></metadataNamespace>
        </metadataFormat>
  </ListMetadataFormats>""", self.stream.getvalue())
        self.assertValidString(self.stream.getvalue())

    def testListMetadataFormatsForIdentifierFile(self):
        jazz = OaiJazz(self.tempdir)
        self.assertWithJazz(jazz)

    def testListMetadataFormatsNonExistingId(self):
        class Observer:
            def getUnique(*args):
                return None
            def getAllMetadataFormats(*args):
                return []
        self.request.args = {'verb': ['ListMetadataFormats'], 'identifier': ['DoesNotExist']}
        self.subject.addObserver(Observer())
        self.observable.any.listMetadataFormats(self.request)
        self.assertTrue("""<error code="idDoesNotExist">The value of the identifier argument is unknown or illegal in this repository.</error>""" in self.stream.getvalue())
        self.assertValidString(self.stream.getvalue())
