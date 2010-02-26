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
from cq2utils import CQ2TestCase, CallTrace

from merescocomponents.oai import OaiAddRecord
from StringIO import StringIO
from lxml.etree import parse

def parseLxml(aString):
    return parse(StringIO(aString)).getroot()

class OaiAddRecordTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.subject = OaiAddRecord()
        self.observer = CallTrace('observert')
        self.observer.getAllMetadataFormats = lambda: []
        self.subject.addObserver(self.observer)

    def testAdd(self):
        self.subject.add('id', 'partName', parseLxml('<empty/>'))

        self.assertEquals(1,len(self.observer.calledMethods))
        self.assertEquals('addOaiRecord', self.observer.calledMethods[0].name)
        self.assertEquals('id', self.observer.calledMethods[0].kwargs['identifier'])
        self.assertEquals([('partName', '', '')], self.observer.calledMethods[0].kwargs['metadataFormats'])
        self.assertEquals(set(), self.observer.calledMethods[0].kwargs['sets'])

    def testAddSetInfo(self):
        header = parseLxml('<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>1</setSpec></header>')
        
        self.subject.add('123', 'oai_dc', header)
        
        self.assertEquals(1,len(self.observer.calledMethods))
        self.assertEquals('addOaiRecord', self.observer.calledMethods[0].name)
        self.assertEquals('123', self.observer.calledMethods[0].kwargs['identifier'])
        self.assertEquals(set([('1','1')]), self.observer.calledMethods[0].kwargs['sets'])
        self.assertEquals([('oai_dc', '', "http://www.openarchives.org/OAI/2.0/")], self.observer.calledMethods[0].kwargs['metadataFormats'])

    def testAddRecognizeNamespace(self):
        header = '<header xmlns="this.is.not.the.right.ns"><setSpec>%s</setSpec></header>'
        self.subject.add('123', 'oai_dc', parseLxml(header % 1))
        header = '<header xmlns="http://www.openarchives.org/OAI/2.0/"><setSpec>%s</setSpec></header>'
        self.subject.add('124', 'oai_dc', parseLxml(header % 1))
        self.assertEquals([('oai_dc', '', "this.is.not.the.right.ns")], self.observer.calledMethods[0].kwargs['metadataFormats'])
        self.assertEquals([('oai_dc', '', "http://www.openarchives.org/OAI/2.0/")], self.observer.calledMethods[1].kwargs['metadataFormats'])

    def testMultipleHierarchicalSets(self):
        spec = "<setSpec>%s</setSpec>"
        header = '<header xmlns="http://www.openarchives.org/OAI/2.0/">%s</header>'
        self.subject.add('124', 'oai_dc', parseLxml(header % (spec % '2:3' + spec % '3:4')))
        self.assertEquals('124', self.observer.calledMethods[0].kwargs['identifier'])
        self.assertEquals([('oai_dc', '', "http://www.openarchives.org/OAI/2.0/")], self.observer.calledMethods[0].kwargs['metadataFormats'])
        self.assertEquals(set([('2:3', '2:3'), ('3:4', '3:4')]), self.observer.calledMethods[0].kwargs['sets'])
    
    def testMetadataPrefixes(self):
        self.subject.add('456', 'oai_dc', parseLxml('<oai_dc:dc xmlns:oai_dc="http://oai_dc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
             xsi:schemaLocation="http://oai_dc http://oai_dc/dc.xsd"/>'))
        self.assertEquals([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc')], self.observer.calledMethods[0].kwargs['metadataFormats'])
        self.subject.add('457', 'dc2', parseLxml('<oai_dc:dc xmlns:oai_dc="http://dc2"/>'))
        self.assertEquals([('dc2', '', 'http://dc2')], self.observer.calledMethods[1].kwargs['metadataFormats'])

    def testMetadataPrefixesFromRootTag(self):
        self.subject.add('456', 'oai_dc', parseLxml('''<oai_dc:dc 
        xmlns:oai_dc="http://oai_dc" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://other
                            http://other.com/file.xsd
                            http://oai_dc 
                            http://oai_dc/dc.xsd">
</oai_dc:dc>'''))
        self.assertEquals([('oai_dc', 'http://oai_dc/dc.xsd', 'http://oai_dc')], self.observer.calledMethods[0].kwargs['metadataFormats'])

    def testIncompletePrefixInfo(self):
        self.subject.add('457', 'dc2', parseLxml('<oai_dc/>'))
        self.assertEquals([('dc2', '', '')], self.observer.calledMethods[0].kwargs['metadataFormats'])

