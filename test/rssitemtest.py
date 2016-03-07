# coding: utf-8
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
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

from seecr.test import SeecrTestCase as TestCase

from meresco.components.rssitem import RssItem
from StringIO import StringIO

class RssItemTest(TestCase):
    def testOne(self):
        item = RssItem(
            nsMap = {},
            title = ('part1', '/dc/title/text()'),
            description = ('part1', '/dc/description/text()'),
            linkTemplate='http://example.org/show?recordId=%(recordId)s&type=%(type)s',
            recordId = ('part2', '/meta/upload/id/text()'),
            type = ('part2', '/meta/type/text()')
        )
        item.addObserver(MockStorage())
        result = "".join(list(item.getRecord('aap')))
        self.assertEqualsWS("""<item>
    <title>Title</title>
    <description>Description</description>
    <link>http://example.org/show?recordId=12%2834%29&amp;type=Type</link>
    <guid>http://example.org/show?recordId=12%2834%29&amp;type=Type</guid>
</item>""", result)

    def testNoDescription(self):
        item = RssItem(
            nsMap = {},
            title = ('part1', '/dc/title/text()'),
            description = ('partNoDescription', '/dc/description/text()'),
            linkTemplate = 'http://www.example.org/'
        )
        item.addObserver(MockStorage())
        result = "".join(list(item.getRecord('aap')))
        self.assertEqualsWS("""<item>
    <title>Title</title>
    <description></description>
    <link>http://www.example.org/</link>
    <guid>http://www.example.org/</guid>
</item>""", result)

    def testPartOfLinkTemplateNotFound(self):
        item = RssItem(
            nsMap = {},
            title = ('part1', '/dc/title/text()'),
            description = ('partNoDescription', '/dc/description/text()'),
            linkTemplate = 'http://www.example.org/%(something)s',
            something = ('part1', '/dc/not/existing/text()'),
        )
        item.addObserver(MockStorage())
        result = "".join(list(item.getRecord('aap')))
        self.assertEqualsWS("""<item>
    <title>Title</title>
    <description></description>
    <link></link>
    <guid></guid>
</item>""", result)

    def testPartOfLinkTemplateNotConfigured(self):
        try:
            item = RssItem(
                nsMap = {},
                title = ('part1', '/dc/title/text()'),
                description = ('partNoDescription', '/dc/description/text()'),
                linkTemplate = 'http://www.example.org/%(notMentioned)s',
            )
            self.fail()
        except TypeError, e:
            self.assertEquals("__init__() takes at least 6 arguments (5 given, missing 'notMentioned')", str(e))

    def testUnicodeInData(self):
        item = RssItem(
            nsMap = {},
            title = ('part1', '/dc/title/text()'),
            description = ('partWithUnicode', '/dc/description/text()'),
            linkTemplate = 'http://www.example.org/%(recordType)s',
            recordType = ('part2', '/meta/type/text()')
        )
        item.addObserver(MockStorage())
        result = "".join(list(item.getRecord('aap')))
        self.assertEqualsWS("""<item>
    <title>Title</title>
    <description>“</description>
    <link>http://www.example.org/Type</link>
    <guid>http://www.example.org/Type</guid>
</item>""", result)

class MockStorage(object):
    def getData(self, identifier, partname):
        if partname == 'part1':
            return '<dc><title>Title</title><description>Description</description></dc>'
        elif partname == 'part2':
            return '<meta><upload><id>12(34)</id></upload><type>Type</type></meta>'
        elif partname == 'partNoDescription':
            return '<dc><title>Title</title></dc>'
        elif partname == 'partWithUnicode':
            return '<dc><title>Title</title><description>&#8220;</description></dc>'


