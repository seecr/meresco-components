# encoding=utf-8
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
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

from cStringIO import StringIO
from meresco.core.observable import Observable, be
from cq2utils import CallTrace, CQ2TestCase
from amara import binderytools
from lxml.etree import _ElementTree, tostring, parse

from meresco.components import XmlParseAmara, XmlPrintAmara, Amara2Lxml, Lxml2Amara, XmlPrintLxml, XmlParseLxml, FileParseLxml

class XmlPumpTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.observer = CallTrace('Observer', ignoredAttributes=['start'])
        self.observable = be(
            (Observable(),
                (XmlParseAmara(),
                    (self.observer, )
                )
            )
        )


    def testInflate(self):
        xmlString = """<tag><content>contents</content></tag>"""
        self.observable.do.add("id", "partName", xmlString)

        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertEquals("add", self.observer.calledMethods[0].name)
        self.assertEquals(("id", "partName"), self.observer.calledMethods[0].args[:2])

        xmlNode = self.observer.calledMethods[0].args[2]
        self.assertEquals('tag', xmlNode.localName)
        self.assertEquals('content', xmlNode.content.localName)

    def testDeflate(self):
        observable = be(
            (Observable(),
                (XmlPrintAmara(),
                    (self.observer, )
                )
            )
        )

        s = """<tag><content>contents</content></tag>"""
        observable.do.aMethodCall("id", "partName", binderytools.bind_string(s).tag)

        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertEquals("aMethodCall", self.observer.calledMethods[0].name)
        self.assertEquals(("id", "partName", s), self.observer.calledMethods[0].args)

    def testAmara2LXml(self):
        class Observer:
            def ape(inner, lxmlNode):
                self.lxmlNode = lxmlNode
        amara2lxml = Amara2Lxml()
        amara2lxml.addObserver(Observer())
        amaraNode = binderytools.bind_string('<a><b>“c</b></a>')
        list(amara2lxml.unknown('ape', amaraNode))
        self.assertEquals(_ElementTree, type(self.lxmlNode))
        self.assertEquals('<a><b>“c</b></a>', tostring(self.lxmlNode, encoding='utf-8'))

    def testLxml2Amara(self):
        class Observer:
            def ape(inner, amaraNode):
                self.amaraNode = amaraNode
        lxml2amara = Lxml2Amara()
        lxml2amara.addObserver(Observer())
        lxmlNode = parse(StringIO('<a><b>“c</b></a>'))
        list(lxml2amara.unknown('ape', lxmlNode))
        self.assertEquals('<a><b>“c</b></a>', self.amaraNode.xml())

    def testXmlParseAmaraRespondsToEveryMessage(self):
        self.observable.do.aMethodCall('do not parse this', '<parse>this</parse>')

        self.assertEquals(1, len(self.observer.calledMethods))
        method = self.observer.calledMethods[0]
        self.assertEquals('aMethodCall', method.name)
        self.assertEquals(2, len(method.args))
        self.assertEquals('do not parse this', method.args[0])
        self.assertEquals('<parse>this</parse>', method.args[1].xml())



    def testTransparency(self):
        deflate = CallTrace('deflated')
        amara = CallTrace('amara')
        lxml = CallTrace('lxml')
        lxml2 = CallTrace('lxml2')
        observable = be(
            (Observable(),
                (XmlParseAmara(),
                    (amara,),
                    (Amara2Lxml(),
                        (XmlPrintLxml(),
                            (lxml, ),
                        ),
                        (Lxml2Amara(),
                            (XmlPrintAmara(),
                                (deflate, ),
                            )
                        )
                    )
                ),
                (XmlParseLxml(),
                    (XmlPrintLxml(),
                        (lxml2, ),
                    ),
                )
            )
        )

        observable.do.something('identifier', 'partName', '<?xml version="1.0"?><a><b>c</b></a>')
        self.assertEqualsWS('<a><b>c</b></a>', amara.calledMethods[0].args[2].xml())
        self.assertEqualsWS('<a><b>c</b></a>', deflate.calledMethods[0].args[2])
        self.assertEqualsWS('<a><b>c</b></a>', lxml.calledMethods[0].args[2])
        self.assertEqualsWS('<a><b>c</b></a>', lxml2.calledMethods[0].args[2])

    def testFileParseLxml(self):
        observable = Observable()
        observer = CallTrace('observer')
        p = FileParseLxml()
        observable.addObserver(p)
        p.addObserver(observer)
        a = StringIO('<a>aaa</a>')
        f = open(self.tempfile, 'w')
        f.write('<b>bbb</b>')
        f.close()
        b = open(self.tempfile)

        observable.do.someMessage(a, b=b)

        lxmlA = observer.calledMethods[0].args[0]
        lxmlB = observer.calledMethods[0].kwargs['b']
        self.assertEquals('<a>aaa</a>', tostring(lxmlA))
        self.assertEquals('<b>bbb</b>', tostring(lxmlB))

