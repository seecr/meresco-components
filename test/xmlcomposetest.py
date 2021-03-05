## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010, 2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012, 2016, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2021 SURF https://www.surf.nl
# Copyright (C) 2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from seecr.test import SeecrTestCase as TestCase
from meresco.components import XmlCompose

class XmlComposeTest(TestCase):
    def testOne(self):
        xmlcompose = XmlCompose(
            template = """<template><one>%(one)s</one><two>%(two)s</two></template>""",
            nsMap = {'ns1': "http://namespaces.org/ns1"},
            one = ('partname1', '/ns1:one/ns1:tag/text()'),
            two = ('partname2', '/two/tag/@name')
        )
        observer = MockStorage()
        xmlcompose.addObserver(observer)

        result = xmlcompose.getRecord("recordId")
        self.assertEqualsWS(result, """<template><one>1</one><two>&lt;one&gt;</two></template>""")

    def testModuloThing(self):
        class SubXmlCompose(XmlCompose):
            def createRecord(self, aDictionary):
                return '|'.join([
                    aDictionary['one'],
                    aDictionary['two'].upper(),
                    aDictionary['three'].swapcase()
                ])
        xmlcompose = SubXmlCompose(
            template = None,
            nsMap = {},
            one = ('partname3', '/root/one/text()'),
            two = ('partname3', '/root/two/text()'),
            three = ('partname3', '/root/three/text()'),
        )
        observer = MockStorage()
        xmlcompose.addObserver(observer)

        result = xmlcompose.getRecord("recordId")
        self.assertEqualsWS(result, """One|TWO|thrEE""")


class MockStorage(object):
    def __init__(self):
        self.timesCalled = 0

    def getData(self, ident, partname):
        self.timesCalled += 1
        if partname == 'partname1':
            return b"""<one xmlns="http://namespaces.org/ns1"><tag>1</tag><tag>2</tag><escaped>&amp;</escaped></one>"""
        elif partname == 'partname2':
            return b"""<two><tag name="&lt;one&gt;">one</tag><tag name="&quot;two'">two</tag></two>"""
        elif partname == 'partname3':
            return b"""<root><one>One</one><two>TWo</two><three>THRee</three></root>"""

