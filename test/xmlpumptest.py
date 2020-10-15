## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012-2014, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012, 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
#
# This file is part of "Meresco Components"
#
# "Meresco Components" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Components" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Components"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from io import StringIO
from meresco.core import Observable
from seecr.test import SeecrTestCase, CallTrace
from weightless.core import be, compose
from lxml.etree import parse, _ElementStringResult, _ElementUnicodeResult, XML
from meresco.components import lxmltostring

from meresco.components import XmlPrintLxml, XmlParseLxml, FileParseLxml


class XmlPumpTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.observer = CallTrace('Observer', ignoredAttributes=['start'])
        self.observable = be(
            (Observable(),
                (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode'),
                    (self.observer, )
                )
            )
        )

    def testParse(self):
        xmlString = """<tag><content>contents</content></tag>"""
        self.observable.do.add(identifier="id", partname="partName", data=xmlString)

        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertEqual("add", self.observer.calledMethods[0].name)
        self.assertEqual("id", self.observer.calledMethods[0].kwargs['identifier'])
        self.assertEqual("partName", self.observer.calledMethods[0].kwargs['partname'])

        xmlNode = self.observer.calledMethods[0].kwargs['lxmlNode']
        self.assertEqualsLxml(XML(xmlString), xmlNode)

    def testParse2(self):
        xmlString = """<tag><content>contents</content></tag>"""
        self.observable.do.add(identifier="id", partname="partName", data=xmlString)
        self.observable.call.add(identifier="id", partname="partName", data=xmlString)
        self.observer.methods['add'] = lambda **kwargs: (x for x in [])
        list(compose(self.observable.all.add(identifier="id", partname="partName", data=xmlString)))
        list(compose(self.observable.any.add(identifier="id", partname="partName", data=xmlString)))

        self.assertEqual(4, len(self.observer.calledMethods))
        for i in range(4):
            xmlNode = self.observer.calledMethods[i].kwargs['lxmlNode']
            self.assertEqualsLxml(XML(xmlString), xmlNode)

    def testParseWithElementStringResult(self):
        xmlString = _ElementStringResult("""<tag><content>contents</content></tag>""", "utf-8")
        self.observable.do.add(identifier="id", partname="partName", data=xmlString)

        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertEqual("add", self.observer.calledMethods[0].name)
        self.assertEqual("id", self.observer.calledMethods[0].kwargs['identifier'])
        self.assertEqual("partName", self.observer.calledMethods[0].kwargs['partname'])

        xmlNode = self.observer.calledMethods[0].kwargs['lxmlNode']
        rootTag = xmlNode.getroot()
        self.assertEqual('tag', rootTag.tag)
        self.assertEqual(['content'], [c.tag for c in rootTag.getchildren()])

    def testParseWithElementUnicodeResult(self):
        xmlString = _ElementUnicodeResult("""<tag><content>conténts</content></tag>""")
        self.observable.do.add(identifier="id", partname="partName", data=xmlString)

        xmlNode = self.observer.calledMethods[0].kwargs['lxmlNode']
        self.assertEqual(['conténts'], xmlNode.xpath('/tag/content/text()'))

    def testParseWithParseOptions(self):
        xmlString = """<tag xmlns:xyz="uri:xyz">
                <content xmlns:xyz="uri:xyz">contents</content>
            </tag>"""
        self.observable.do.add(identifier="id", partname="partName", data=xmlString)
        self.assertEqual(xmlString, lxmltostring(self.observer.calledMethods[0].kwargs['lxmlNode']))

        self.observable = be(
            (Observable(),
                (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode', parseOptions=dict(remove_blank_text=True, ns_clean=True)),
                    (self.observer,)
                )
            )
        )
        self.observable.do.add(identifier="id", partname="partName", data=xmlString)
        self.assertEqual("""<tag xmlns:xyz="uri:xyz"><content>contents</content></tag>""", lxmltostring(self.observer.calledMethods[1].kwargs['lxmlNode']))

    def testXmlPrintLxml(self):
        observable = Observable()
        xmlprintlxml = XmlPrintLxml(fromKwarg='lxmlNode', toKwarg="data")
        observer = CallTrace('observer', emptyGeneratorMethods=['someMessage'])
        xmlprintlxml.addObserver(observer)
        observable.addObserver(xmlprintlxml)
        list(compose(observable.all.someMessage(lxmlNode=parse(StringIO('<a><b>“c</b></a>')))))
        self.assertEqual(['someMessage'], observer.calledMethodNames())
        self.assertEqual(['data'], list(observer.calledMethods[0].kwargs.keys()))
        self.assertEqual('''<a>
  <b>“c</b>
</a>
''', observer.calledMethods[0].kwargs['data'])

    def testXmlPrintLxmlPrettyPrintFalse(self):
        observable = Observable()
        xmlprintlxml = XmlPrintLxml(fromKwarg='lxmlNode', toKwarg="data", pretty_print=False)
        observer = CallTrace('observer', emptyGeneratorMethods=['someMessage'])
        xmlprintlxml.addObserver(observer)
        observable.addObserver(xmlprintlxml)
        list(compose(observable.all.someMessage(lxmlNode=parse(StringIO('<a><b>“c</b></a>')))))
        self.assertEqual(['someMessage'], observer.calledMethodNames())
        self.assertEqual(['data'], list(observer.calledMethods[0].kwargs.keys()))
        self.assertEqual('''<a><b>“c</b></a>''', observer.calledMethods[0].kwargs['data'])

    def testTransparency(self):
        lxml = CallTrace('lxml')
        lxml2 = CallTrace('lxml2')
        observable = be(
            (Observable(),
                (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode'),
                    (XmlPrintLxml(fromKwarg='lxmlNode', toKwarg='data'),
                        (lxml, ),
                        (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode'),
                            (XmlPrintLxml(fromKwarg='lxmlNode', toKwarg='data'),
                                (lxml2,),
                            )
                        )
                    ),
                )
            )
        )

        observable.do.something(identifier='identifier', partname='partName', data='<?xml version="1.0"?><a><b>c</b></a>')
        self.assertEqualsWS('<a><b>c</b></a>', lxml.calledMethods[0].kwargs['data'])
        self.assertEqualsWS('<a><b>c</b></a>', lxml2.calledMethods[0].kwargs['data'])

    def testMissingFromKwargDoesNothing(self):
        observer = CallTrace()
        observable = be(
            (Observable(),
                (XmlPrintLxml(fromKwarg='lxmlNode', toKwarg='data'),
                    (observer, )
                )
            )
        )

        observable.do.something('identifier', 'partname', parse(StringIO('<a/>')))
        self.assertEqual(1, len(observer.calledMethods))
        self.assertEqual("<class 'lxml.etree._ElementTree'>", str(type(observer.calledMethods[0].args[2])))

    def testFileParseLxml(self):
        observable = Observable()
        observer = CallTrace('observer')
        p = FileParseLxml(fromKwarg='filedata', toKwarg='lxmlNode')
        observable.addObserver(p)
        p.addObserver(observer)
        a = StringIO('<a>aaa</a>')
        observable.do.someMessage(filedata=a)
        lxmlA = observer.calledMethods[0].kwargs['lxmlNode']
        self.assertEqual('<a>aaa</a>', lxmltostring(lxmlA))

        with open(self.tempfile, 'w') as f:
            f.write('<b>bbb</b>')
        with open(self.tempfile) as b:
            observable.do.someMessage(filedata=b)
            lxmlB = observer.calledMethods[1].kwargs['lxmlNode']
            self.assertEqual('<b>bbb</b>', lxmltostring(lxmlB))

    def testRenameKwargOnConvert(self):
        observer = CallTrace()
        observable = be(
            (Observable(),
                (XmlPrintLxml(fromKwarg='lxmlNode', toKwarg='dataString'),
                    (observer,),
                )
            )
        )
        observable.do.something('identifier', 'partname', lxmlNode=parse(StringIO('<someXml/>')))
        self.assertEqual("something('identifier', 'partname', dataString='<someXml/>\n')", str(observer.calledMethods[0]))

        observable.do.something('identifier', 'partname', someKwarg=1)
        self.assertEqual("something('identifier', 'partname', someKwarg=1)", str(observer.calledMethods[1]))

    def testToKwargDefaultsToFromKwarg(self):
        observer = CallTrace()
        observable = be(
            (Observable(),
                (XmlPrintLxml(fromKwarg='data'),
                    (observer,),
                )
            )
        )
        observable.do.something('identifier', 'partname', data=parse(StringIO('<someXml/>')))
        self.assertEqual("something('identifier', 'partname', data='<someXml/>\n')", str(observer.calledMethods[0]))

    def testLxmltostring(self):
        from lxml.etree import tostring
        uri = "Baháma's"
        xml = """<root><sub><subsub attribute="%s">%s</subsub></sub></root>""" % (uri, uri)
        lxmlNode = parse(StringIO(xml))
        subnode = lxmlNode.xpath("sub")[0]
        self.assertEqual(b"""<sub><subsub attribute="Bah\xc3\xa1ma's">Bah\xc3\xa1ma's</subsub></sub>""", lxmltostring(subnode).encode('utf-8'))
        subsubnode = lxmlNode.xpath("sub/subsub")[0]
        self.assertEqual(b"""<subsub attribute="Bah&#xE1;ma's">Bah\xc3\xa1ma's</subsub>""", tostring(subsubnode, encoding='UTF-8'))
        self.assertEqual(b"""<subsub attribute="Bah\xc3\xa1ma's">Bah\xc3\xa1ma's</subsub>""", lxmltostring(subsubnode).encode('utf-8'))


    def testLxmltostringFixes(self):
        from meresco.components.xmlpump import _fixLxmltostringRootElement

        self.assertEqual('<root><sub ...', _fixLxmltostringRootElement('<root><sub ...'))
        self.assertEqual('<root attrib="aap&amp;noot"><sub ...',
                _fixLxmltostringRootElement('<root attrib="aap&amp;noot"><sub ...'))
        self.assertEqual('<root attrib="aap&euro;noot"><sub ...',
                _fixLxmltostringRootElement('<root attrib="aap&euro;noot"><sub ...'))
        self.assertEqual('<root attrib="ĳs"><sub ...',
                _fixLxmltostringRootElement('<root attrib="&#307;s"><sub ...'))
        self.assertEqual('<root attrib="ĳs"><sub ...',
                _fixLxmltostringRootElement('<root attrib="&#x133;s"><sub ...'))
        self.assertEqual('<root attrib="ĳs"><sub attrib="&#x133;s">...',
                _fixLxmltostringRootElement('<root attrib="&#x133;s"><sub attrib="&#x133;s">...'))
