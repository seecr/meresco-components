from cq2utils import CQ2TestCase, CallTrace

from os.path import join
from lxml.etree import parse
from StringIO import StringIO

from bzv import XmlDocumentAdapter

class XmlDocumentAdapterTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.adapter = XmlDocumentAdapter()
        self.observer = CallTrace('observer')
        self.adapter.addObserver(self.observer)

    def testValidFile(self):

        self.assertEquals(('', ''), self.adapter._splitFilename("some_file"))
        self.assertEquals(('', ''), self.adapter._splitFilename("repository:identifier"))
        self.assertEquals(('repository', 'identifier'), self.adapter._splitFilename("repository:identifier.record"))
        self.assertEquals(('repo', 'Even\tTabs and <spaces> are /escaped properly'), self.adapter._splitFilename("repo:Even%09Tabs and <spaces> are %2Fescaped properly.record"))

    def testCreateXml(self):
        filename = 'repository:some:identifier:1.record'

        self.adapter.add(identifier=filename, lxmlNode=parse(StringIO('<record/>')))

        self.assertEquals("add(identifier='some:identifier:1', lxmlNode=<etree._ElementTree>)", str(self.observer.calledMethods[0]))

        lxmlNode = self.observer.calledMethods[0].kwargs['lxmlNode']
        self.assertEquals(3, len(lxmlNode.xpath('/document:document/document:part', namespaces={'document':'http://meresco.com/namespace/harvester/document'})))

        header = lxmlNode.xpath('/document:document/document:part[@name="header"]/text()', namespaces={'document':'http://meresco.com/namespace/harvester/document'})[0]
        self.assertEqualsWS("""<header xmlns="http://www.openarchives.org/OAI/2.0/">
            <identifier>some:identifier:1</identifier>
        </header>""", header)

        meta = lxmlNode.xpath('/document:document/document:part[@name="meta"]/text()', namespaces={'document':'http://meresco.com/namespace/harvester/document'})[0]
        self.assertEqualsWS("""<meta xmlns="http://meresco.com/namespace/harvester/meta">
        <upload><id>repository:some:identifier:1</id></upload>
        <record><id>some:identifier:1</id></record>
        <repository><id>repository</id></repository></meta>""", meta)

        metadata = lxmlNode.xpath('/document:document/document:part[@name="metadata"]/text()', namespaces={'document':'http://meresco.com/namespace/harvester/document'})[0]
        self.assertEqualsWS("""<metadata xmlns="http://www.openarchives.org/OAI/2.0/"><record/></metadata>""", metadata)
