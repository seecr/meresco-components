# -*- coding=utf-8 -*-
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
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase, CallTrace
from meresco.core import Observable

from weightless.core import be, compose

from meresco.components import XmlXPath, XmlParseLxml
from meresco.components.xmlxpath import lxmlElementUntail
from lxml.etree import parse, ElementTree, _ElementTree as ElementTreeType, tostring
from StringIO import StringIO
import sys


class XmlXPathTest(SeecrTestCase):

    def createXmlXPath(self, xpathList, nsMap):
        self.observer = CallTrace('observer',ignoredAttributes=['start'] )
        self.observable = be(
            (Observable(),
                (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode'),
                    (XmlXPath(xpathList, nsMap),
                        (self.observer, ),
                    )
                )
            )
        )

    def testSimpleXPath(self):
        self.createXmlXPath(['/root/path'], {})

        xml = '<root><path><to>me</to></path>\n</root>'
        self.observable.do.test('een tekst', data=xml)

        self.assertEquals(1, len(self.observer.calledMethods))
        method = self.observer.calledMethods[0]
        self.assertEquals('test', method.name)
        self.assertEquals(1, len(method.args))
        self.assertEquals('een tekst', method.args[0])
        self.assertEqualsWS('<path><to>me</to></path>', tostring(method.kwargs['lxmlNode']))
        self.assertEquals('<path><to>me</to></path>', tostring(method.kwargs['lxmlNode']))

    def testSimpleXPathWithUnicodeChars(self):
        self.createXmlXPath(['/root/text()'], {})

        self.observable.do.test('een tekst', data='<root>&lt;tag&gt;t€xt&lt;/tag&gt;</root>')
        method = self.observer.calledMethods[0]
        self.assertEquals('<tag>t€xt</tag>', method.kwargs['lxmlNode'])

    def testElementInKwargs(self):
        self.createXmlXPath(['/root/path'], {})

        self.observable.do.aMethod('otherArgument', data='<root><path><to>me</to></path></root>', otherKeyword='okay')

        self.assertEquals(1, len(self.observer.calledMethods))
        method = self.observer.calledMethods[0]
        self.assertEquals('aMethod', method.name)
        self.assertEquals(1, len(method.args))
        self.assertEquals(set(['otherKeyword', 'lxmlNode']), set(method.kwargs.keys()))
        self.assertEqualsWS('<path><to>me</to></path>', tostring(method.kwargs['lxmlNode']))

    def testNoElementInArgumentsPassesOn(self):
        self.createXmlXPath(['/root/path'], {})

        self.observable.do.aMethod('do not xpath me')

        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertEquals('do not xpath me', self.observer.calledMethods[0].args[0])

    def testXPathWithNamespaces(self):
        self.createXmlXPath(['/a:root/b:path/c:findme'], {'a':'ns1', 'b':'ns2', 'c':'ns3'})

        self.observable.do.aMethod(data="""<root xmlns="ns1" xmlns:two="ns2">
            <two:path><findme xmlns="ns3">Found</findme></two:path></root>""")

        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertEquals('Found', self.observer.calledMethods[0].kwargs['lxmlNode'].xpath('text()')[0])


    def testXPathWithConditions(self):
        self.createXmlXPath(['/root/element[pick="me"]/data'], {})

        self.observable.do.aMethod(data="""<root>
    <element>
        <pick>not me</pick>
        <data>Not this data</data>
    </element>
    <element>
        <pick>me</pick>
        <data>This data</data>
    </element>
</root>""")

        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertEqualsWS('<data>This data</data>', tostring(self.observer.calledMethods[0].kwargs['lxmlNode']))

    def testXPathWithMultipleResults(self):
        self.createXmlXPath(['/root/element/data'], {})

        self.observable.do.aMethod(data="""<root>
    <element>
        <data>one</data>
    </element>
    <element>
        <data>two</data>
    </element>
</root>""")
        self.assertEquals(2, len(self.observer.calledMethods))
        self.assertEqualsWS('<data>one</data>', tostring(self.observer.calledMethods[0].kwargs['lxmlNode']))
        self.assertEqualsWS('<data>two</data>', tostring(self.observer.calledMethods[1].kwargs['lxmlNode']))

    def testXPathWithNoResults(self):
        self.createXmlXPath(['/does/not/exist'], {})

        self.observable.do.aMethod(data="""<some><element>data</element></some>""")
        self.assertEquals(0, len(self.observer.calledMethods))

    def testOnlyOneXMLAllowed(self):
        self.createXmlXPath('/root', {})
        try:
            self.observable.do.aMethod(parse(StringIO("<somexml/>")), data="<otherxml/>")
            self.fail()
        except AssertionError, e:
            self.assertEquals('Can only handle one ElementTree in argument list.', str(e))

    def testDoNotChangeArgs(self):
        xmlXPath = XmlXPath(['/a'])
        arg = parse(StringIO('<a>a</a>'))
        list(compose(xmlXPath.all_unknown('message', arg)))
        self.assertEquals('<a>a</a>', tostring(arg))

    def testNamespaces(self):
        xmlXPath = XmlXPath(['/a:aNode/b:bNode'], {'a':'aNamespace', 'b':'bNamespace' })
        arg = parse(StringIO('<aNode xmlns="aNamespace"><bNode xmlns="bNamespace">ccc</bNode></aNode>'))
        observer = CallTrace('Observer')
        observable = Observable()
        observable.addObserver(xmlXPath)
        xmlXPath.addObserver(observer)

        observable.do.message(arg)

        message = observer.calledMethods[0]
        self.assertEquals('message', message.name)
        newNode = message.args[0]
        self.assertEqualsWS('<bNode xmlns="bNamespace">ccc</bNode>', tostring(newNode))

        newNamespaces = newNode.getroot().nsmap
        nameSpacesAfterParsing = parse(StringIO(tostring(newNode))).getroot().nsmap
        self.assertEquals(nameSpacesAfterParsing, newNamespaces)

    def testFindUsingMultipleXPaths(self):
        self.createXmlXPath(['/does/not/exist', '/a/b', '/a/b/c'], {})

        self.observable.do.test(data='<a><b><c>one</c></b><b><d>two</d></b></a>')

        self.assertEquals(3, len(self.observer.calledMethods))
        allResults = []
        for method in self.observer.calledMethods:
            allResults.append(method.kwargs['lxmlNode'])
        self.assertEqualsWS('<b><c>one</c></b>', tostring(allResults[0]))
        self.assertEqualsWS('<b><d>two</d></b>', tostring(allResults[1]))
        self.assertEqualsWS('<c>one</c>', tostring(allResults[2]))

    def testTestWithCondition(self):
        self.createXmlXPath(['/a/*[not(self::b) and not(self::c)]'], {})

        self.observable.do.test(data='<a><b>zero</b><c>one</c><d>two</d></a>')

        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertEqualsWS('<d>two</d>', tostring(self.observer.calledMethods[0].kwargs['lxmlNode']))

    def testTestWithConditionAndNS(self):
        self.createXmlXPath(['/a:a/*[not(self::a:b) and not(self::a:c)]'], {"a":"aSpace"})

        self.observable.do.test(data='<z:a xmlns:z="aSpace"><z:b>zero</z:b><z:c>one</z:c><z:d>two</z:d></z:a>')

        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertEqualsWS('two', self.observer.calledMethods[0].kwargs['lxmlNode'].xpath("text()")[0])

    def testXPathReturnsString(self):
        xpath = XmlXPath(['/a/t/text()'])
        inputNode = parse(StringIO('<a><t>some text &amp; some &lt;entities&gt;</t></a>'))

        observable = Observable()
        observer = CallTrace('observer')
        observable.addObserver(xpath)
        xpath.addObserver(observer)

        observable.do.aMethod(lxmlNode=inputNode)
        self.assertEquals(1, len(observer.calledMethods))
        result = observer.calledMethods[0].kwargs
        self.assertEquals({'lxmlNode': 'some text & some <entities>'}, result)

    def testTailTakeCareOfWithoutAffectingOriginal(self):
        observer = CallTrace('observer')
        observable = be(
            (Observable(),
                (XmlXPath(
                        ['/myns:root/myns:path'],
                        {'myns': 'http://myns.org/'}
                    ),
                    (observer, ),
                )
            )
        )

        XML = """\
<root xmlns:myns="http://myns.org/" xmlns="http://myns.org/">
    <myns:path>
        <to>me</to>
    </myns:path>\n
</root>"""

        lxmlNode = parse(StringIO(XML))
        self.assertEquals(XML, tostring(lxmlNode))
        list(compose(observable.all.test('een tekst', lxmlNode=lxmlNode)))

        self.assertEquals(1, len(observer.calledMethods))
        method = observer.calledMethods[0]
        self.assertEquals('test', method.name)
        self.assertEqualsWS('<myns:path xmlns:myns="http://myns.org/" xmlns="http://myns.org/"><to>me</to></myns:path>', tostring(method.kwargs['lxmlNode']))
        self.assertEquals("""\
<myns:path xmlns:myns="http://myns.org/" xmlns="http://myns.org/">
        <to>me</to>
    </myns:path>""", tostring(method.kwargs['lxmlNode']))

        self.assertEquals(XML, tostring(lxmlNode))


    def testLxmlElementUntail(self):
        lxmlNode = parse(StringIO('<myns:root xmlns:myns="http://myns.org/" xmlns="http://myns.org/"><a>b</a></myns:root>'))
        element = lxmlNode.xpath('/myns:root/myns:a', namespaces={'myns': 'http://myns.org/'})[0]
        self.assertEquals(None, element.tail)
        newElement = lxmlElementUntail(element)
        self.assertTrue(newElement is element)

        lxmlNode = parse(StringIO('<myns:root xmlns:myns="http://myns.org/" xmlns="http://myns.org/"><a><b>c</b>\n\n</a>\n\n\n\n</myns:root>'))
        element = lxmlNode.xpath('/myns:root/myns:a', namespaces={'myns': 'http://myns.org/'})[0]
        self.assertEquals('\n\n\n\n', element.tail)
        newElement = lxmlElementUntail(element)
        self.assertFalse(newElement is element)
        self.assertEquals(None, newElement.tail)
        self.assertEquals('<a xmlns="http://myns.org/"><b>c</b>\n\n</a>', tostring(newElement))

