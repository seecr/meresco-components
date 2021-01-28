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
# Copyright (C) 2010, 2012 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
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

import sys
from io import StringIO
from lxml.etree import parse, ElementTree, _ElementTree as ElementTreeType
from meresco.components import lxmltostring

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import be, compose
from meresco.core import Observable
from meresco.components import XmlXPath, XmlParseLxml
from meresco.components.xmlxpath import lxmlElementUntail


class XmlXPathTest(SeecrTestCase):
    def createXmlXPath(self, xpathList, nsMap):
        self.observer = CallTrace('observer', ignoredAttributes=['start'])
        self.observable = be(
            (Observable(),
                (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode'),
                    (XmlXPath(xpathList, fromKwarg='lxmlNode', namespaces=nsMap),
                        (self.observer, ),
                    )
                )
            )
        )

    def testSimpleXPath(self):
        self.createXmlXPath(['/root/path'], {})

        xml = '<root><path><to>me</to></path>\n</root>'
        self.observable.do.test('een tekst', data=xml)

        self.assertEqual(1, len(self.observer.calledMethods))
        method = self.observer.calledMethods[0]
        self.assertEqual('test', method.name)
        self.assertEqual(1, len(method.args))
        self.assertEqual('een tekst', method.args[0])
        self.assertEqualsWS('<path><to>me</to></path>', lxmltostring(method.kwargs['lxmlNode']))
        self.assertEqual('<path><to>me</to></path>', lxmltostring(method.kwargs['lxmlNode']))

    def testSimpleXPathWithUnicodeChars(self):
        self.createXmlXPath(['/root/text()'], {})

        self.observable.do.test('een tekst', data='<root>&lt;tag&gt;t€xt&lt;/tag&gt;</root>')
        method = self.observer.calledMethods[0]
        self.assertEqual('<tag>t€xt</tag>', method.kwargs['lxmlNode'])

    def testElementInKwargs(self):
        self.createXmlXPath(['/root/path'], {})

        self.observable.do.aMethod('otherArgument', data='<root><path><to>me</to></path></root>', otherKeyword='okay')

        self.assertEqual(1, len(self.observer.calledMethods))
        method = self.observer.calledMethods[0]
        self.assertEqual('aMethod', method.name)
        self.assertEqual(1, len(method.args))
        self.assertEqual(set(['otherKeyword', 'lxmlNode']), set(method.kwargs.keys()))
        self.assertEqualsWS('<path><to>me</to></path>', lxmltostring(method.kwargs['lxmlNode']))

    def testFromKwargMissingRaisesKeyError(self):
        self.createXmlXPath(['/root/path'], {})
        try:
            self.observable.do.aMethod('do not xpath me')
            self.fail('should not get here')
        except KeyError as e:
            self.assertEqual("'lxmlNode'", str(e))

    def testXPathWithNamespaces(self):
        self.createXmlXPath(['/a:root/b:path/c:findme'], {'a':'ns1', 'b':'ns2', 'c':'ns3'})

        self.observable.do.aMethod(data="""<root xmlns="ns1" xmlns:two="ns2">
            <two:path><findme xmlns="ns3">Found</findme></two:path></root>""")

        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertEqual('Found', self.observer.calledMethods[0].kwargs['lxmlNode'].xpath('text()')[0])

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

        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertEqualsWS('<data>This data</data>', lxmltostring(self.observer.calledMethods[0].kwargs['lxmlNode']))

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
        self.assertEqual(2, len(self.observer.calledMethods))
        self.assertEqualsWS('<data>one</data>', lxmltostring(self.observer.calledMethods[0].kwargs['lxmlNode']))
        self.assertEqualsWS('<data>two</data>', lxmltostring(self.observer.calledMethods[1].kwargs['lxmlNode']))

    def testXPathWithNoResults(self):
        self.createXmlXPath(['/does/not/exist'], {})

        self.observable.do.aMethod(data="""<some><element>data</element></some>""")
        self.assertEqual(0, len(self.observer.calledMethods))

    def testDoNotChangeOriginal(self):
        xmlXPath = XmlXPath(['/a'], fromKwarg='lxmlNode')
        lxmlNode = parse(StringIO('<a>a</a>'))
        list(compose(xmlXPath.all_unknown('message', lxmlNode=lxmlNode)))
        self.assertEqual('<a>a</a>', lxmltostring(lxmlNode))

    def testNamespaces(self):
        xmlXPath = XmlXPath(['/a:aNode/b:bNode'], fromKwarg='lxmlNode', namespaces={'a':'aNamespace', 'b':'bNamespace' })
        lxmlNode = parse(StringIO('<aNode xmlns="aNamespace"><bNode xmlns="bNamespace">ccc</bNode></aNode>'))
        observer = CallTrace('Observer')
        observable = Observable()
        observable.addObserver(xmlXPath)
        xmlXPath.addObserver(observer)

        observable.do.message(lxmlNode=lxmlNode)

        message = observer.calledMethods[0]
        self.assertEqual('message', message.name)
        newNode = message.kwargs['lxmlNode']
        self.assertEqualsWS('<bNode xmlns="bNamespace">ccc</bNode>', lxmltostring(newNode))

        newNamespaces = newNode.getroot().nsmap
        nameSpacesAfterParsing = parse(StringIO(lxmltostring(newNode))).getroot().nsmap
        self.assertEqual(nameSpacesAfterParsing, newNamespaces)

    def testFindUsingMultipleXPaths(self):
        self.createXmlXPath(['/does/not/exist', '/a/b', '/a/b/c'], {})

        self.observable.do.test(data='<a><b><c>one</c></b><b><d>two</d></b></a>')

        self.assertEqual(3, len(self.observer.calledMethods))
        allResults = []
        for method in self.observer.calledMethods:
            allResults.append(method.kwargs['lxmlNode'])
        self.assertEqualsWS('<b><c>one</c></b>', lxmltostring(allResults[0]))
        self.assertEqualsWS('<b><d>two</d></b>', lxmltostring(allResults[1]))
        self.assertEqualsWS('<c>one</c>', lxmltostring(allResults[2]))

    def testTestWithCondition(self):
        self.createXmlXPath(['/a/*[not(self::b) and not(self::c)]'], {})

        self.observable.do.test(data='<a><b>zero</b><c>one</c><d>two</d></a>')

        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertEqualsWS('<d>two</d>', lxmltostring(self.observer.calledMethods[0].kwargs['lxmlNode']))

    def testTestWithConditionAndNS(self):
        self.createXmlXPath(['/a:a/*[not(self::a:b) and not(self::a:c)]'], {"a":"aSpace"})

        self.observable.do.test(data='<z:a xmlns:z="aSpace"><z:b>zero</z:b><z:c>one</z:c><z:d>two</z:d></z:a>')

        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertEqualsWS('two', self.observer.calledMethods[0].kwargs['lxmlNode'].xpath("text()")[0])

    def testXPathReturnsString(self):
        xpath = XmlXPath(['/a/t/text()'], fromKwarg="lxmlNode")
        inputNode = parse(StringIO('<a><t>some text &amp; some &lt;entities&gt;</t></a>'))

        observable = Observable()
        observer = CallTrace('observer')
        observable.addObserver(xpath)
        xpath.addObserver(observer)

        observable.do.aMethod(lxmlNode=inputNode)
        self.assertEqual(1, len(observer.calledMethods))
        result = observer.calledMethods[0].kwargs
        self.assertEqual({'lxmlNode': 'some text & some <entities>'}, result)

    def testTailTakenCareOfWithoutAffectingOriginal(self):
        observer = CallTrace('observer', methods={'test': lambda *args, **kwargs: (x for x in [])})
        observable = be(
            (Observable(),
                (XmlXPath(
                        ['/myns:root/myns:path'],
                        fromKwarg='lxmlNode',
                        namespaces={'myns': 'http://myns.org/'}
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
        self.assertEqual(XML, lxmltostring(lxmlNode))
        list(compose(observable.all.test('een tekst', lxmlNode=lxmlNode)))

        self.assertEqual(1, len(observer.calledMethods))
        method = observer.calledMethods[0]
        self.assertEqual('test', method.name)
        self.assertEqualsWS('<myns:path xmlns:myns="http://myns.org/" xmlns="http://myns.org/"><to>me</to></myns:path>', lxmltostring(method.kwargs['lxmlNode']))
        self.assertEqual("""\
<myns:path xmlns:myns="http://myns.org/" xmlns="http://myns.org/">
        <to>me</to>
    </myns:path>""", lxmltostring(method.kwargs['lxmlNode']))

        self.assertEqual(XML, lxmltostring(lxmlNode))


    def testLxmlElementUntail(self):
        lxmlNode = parse(StringIO('<myns:root xmlns:myns="http://myns.org/" xmlns="http://myns.org/"><a>b</a></myns:root>'))
        element = lxmlNode.xpath('/myns:root/myns:a', namespaces={'myns': 'http://myns.org/'})[0]
        self.assertEqual(None, element.tail)
        newElement = lxmlElementUntail(element)
        self.assertTrue(newElement is element)

        lxmlNode = parse(StringIO('<myns:root xmlns:myns="http://myns.org/" xmlns="http://myns.org/"><a><b>c</b>\n\n</a>\n\n\n\n</myns:root>'))
        element = lxmlNode.xpath('/myns:root/myns:a', namespaces={'myns': 'http://myns.org/'})[0]
        self.assertEqual('\n\n\n\n', element.tail)
        newElement = lxmlElementUntail(element)
        self.assertFalse(newElement is element)
        self.assertEqual(None, newElement.tail)
        self.assertEqual('<a xmlns="http://myns.org/"><b>c</b>\n\n</a>', lxmltostring(newElement))

