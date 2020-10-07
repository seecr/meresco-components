## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2013, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2015 SURF http://www.surf.nl
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
from urllib.parse import urlencode
from io import StringIO
from lxml.etree import parse

from testhelpers import Response, Hit
from meresco.components.rss import Rss

from weightless.core import consume, asString

from cqlparser import cqlToExpression

RSS_HEAD = """HTTP/1.0 200 OK
Content-Type: application/rss+xml; charset=utf-8

<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
%s
</channel>
</rss>"""

RSS = RSS_HEAD % """<title>Test title</title>
<description>Test description</description>
<link>http://www.example.org</link>
%s
"""

class RssTest(SeecrTestCase):

    def testNoResults(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        def executeQuery(**kwargs):
            return Response(total=0, hits=[])
            yield
        observer.methods['executeQuery'] = executeQuery

        rss = Rss(
            title = 'Test title',
            description = 'Test description',
            link = 'http://www.example.org',
            sortKeys = 'date,,1',
            maximumRecords = '15',
        )
        rss.addObserver(observer)

        result = asString(rss.handleRequest(RequestURI='/?query=aQuery'))
        self.assertEqualsWS(RSS % '', result)

    def testOneResult(self):
        observer = CallTrace(
            returnValues={
                'getRecord': '<item><title>Test Title</title><link>Test Identifier</link><description>Test Description</description></item>',
            },
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])

        def executeQuery(**kwargs):
            return Response(total=1, hits=[Hit(1)])
            yield
        observer.methods['executeQuery'] = executeQuery

        rss = Rss(
            title = 'Test title',
            description = 'Test description',
            link = 'http://www.example.org',
            sortKeys = 'date,,1',
            maximumRecords = '15',
        )
        rss.addObserver(observer)

        result = asString(rss.handleRequest(RequestURI='/?query=aQuery'))
        self.assertEqualsWS(RSS % """<item>
        <title>Test Title</title>
        <link>Test Identifier</link>
        <description>Test Description</description>
        </item>""", result)

    def testError(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        def executeQuery(**kwargs):
            return Response(total=0, hits=[])
            yield
        observer.methods['executeQuery'] = executeQuery
        rss = Rss(
            title = 'Test title',
            description = 'Test description',
            link = 'http://www.example.org',
        )
        rss.addObserver(observer)
        result = asString(rss.handleRequest(RequestURI='/?query=aQuery%29')) #%29 == ')'

        xml = parse(StringIO(result[result.index("<rss"):]))
        self.assertEqual(['Test title'], xml.xpath('/rss/channel/title/text()'))
        self.assertEqual(['Test description'], xml.xpath('/rss/channel/description/text()'))

    def testErrorNoQuery(self):
        rss = Rss(
            title = 'Test title',
            description = 'Test description',
            link = 'http://www.example.org',
        )
        result = asString(rss.handleRequest(RequestURI='/'))

        xml = parse(StringIO(result[result.index("<rss"):]))
        self.assertEqual(['ERROR Test title'], xml.xpath('/rss/channel/title/text()'))
        self.assertEqual(["An error occurred 'MANDATORY parameter 'query' not supplied or empty'"], xml.xpath('/rss/channel/description/text()'))


    def assertMaxAndSort(self, maximumRecords, sortKey, sortDirection, rssArgs, sruArgs):
        rss = Rss(
            title = 'Test title',
            description = 'Test description',
            link = 'http://www.example.org',
            **rssArgs
        )
        recordIds = []
        def getRecord(identifier):
            recordIds.append(identifier)
            return '<item/>'

        def executeQuery(start, stop, *args, **kwargs):
            response = Response(total=50, hits=[Hit(i) for i in range(start, stop)])
            return response
            yield
        observer = CallTrace(
            methods={
                'executeQuery': executeQuery,
                'getRecord': getRecord,
            },
            ignoredAttributes=['extraResponseData', 'echoedExtraRequestData'])
        rss.addObserver(observer)

        consume(rss.handleRequest(RequestURI='/?query=aQuery&' + urlencode(sruArgs)))

        method = observer.calledMethods[0]
        self.assertEqual('executeQuery', method.name)
        if sortKey is not None:
            self.assertEqual([{'sortBy': sortKey, 'sortDescending': sortDirection}], method.kwargs['sortKeys'])
        else:
            self.assertEqual(None, method.kwargs['sortKeys'])
        self.assertEqual(maximumRecords, len(recordIds))

    def testMaxAndSort(self):
        self.assertMaxAndSort(10, None, None, rssArgs={}, sruArgs={})
        self.assertMaxAndSort(15, None, None, rssArgs={'maximumRecords':'15'}, sruArgs={})
        self.assertMaxAndSort(20, None, None, rssArgs={'maximumRecords':'15'}, sruArgs={'maximumRecords':'20'})
        self.assertMaxAndSort(20, None, None, rssArgs={}, sruArgs={'maximumRecords':'20'})

        self.assertMaxAndSort(10, 'sortable', True, rssArgs={'sortKeys':'sortable,,1'}, sruArgs={})
        self.assertMaxAndSort(10, 'othersortable', False, rssArgs={'sortKeys':'sortable,,1'}, sruArgs={'sortKeys':'othersortable,,0'})
        self.assertMaxAndSort(10, 'othersortable', False, rssArgs={}, sruArgs={'sortKeys':'othersortable,,0'})

    def testContentType(self):
        observer = CallTrace(
            returnValues={'executeQuery': (0, [])},
            ignoredAttributes=['extraResponseData', 'echoedExtraRequestData'])
        rss = Rss(title = 'Title', description = 'Description', link = 'Link')
        rss.addObserver(observer)

        result = "".join(rss.handleRequest())
        self.assertTrue('Content-Type: application/rss+xml' in result, result)

    def testWebQueryUsage(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        def executeQuery(**kwargs):
            return Response(total=0, hits=[])
            yield
        observer.methods['executeQuery'] = executeQuery
        rss = Rss(title = 'Title', description = 'Description', link = 'Link')
        rss.addObserver(observer)

        consume(rss.handleRequest(RequestURI='/?query=one+two'))
        self.assertEqual(['executeQuery'], [m.name for m in observer.calledMethods])
        self.assertEqual(None, observer.calledMethods[0].kwargs['sortKeys'])
        self.assertEqual(0, observer.calledMethods[0].kwargs['start'])
        self.assertEqual(10, observer.calledMethods[0].kwargs['stop'])

    def testAntiUnaryClauseIsPassedToWebQuery(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        def executeQuery(**kwargs):
            return Response(total=0, hits=[])
            yield
        observer.methods['executeQuery'] = executeQuery
        rss = Rss(title='Title', description='Description', link='Link', antiUnaryClause='antiunary')
        rss.addObserver(observer)

        consume(rss.handleRequest(RequestURI='/?query=not+fiets'))

        self.assertEqual(['executeQuery'], [m.name for m in observer.calledMethods])
        self.assertEqual(None, observer.calledMethods[0].kwargs['sortKeys'])
        self.assertEqual(0, observer.calledMethods[0].kwargs['start'])
        self.assertEqual(10, observer.calledMethods[0].kwargs['stop'])
        self.assertEqual(cqlToExpression("antiunary NOT fiets"), observer.calledMethods[0].kwargs['query'])

    def testEmptyQueryWithAntiUnaryClauseIsPassedToWebQuery(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        def executeQuery(**kwargs):
            return Response(total=0, hits=[])
            yield
        observer.methods['executeQuery'] = executeQuery
        rss = Rss(title='Title', description='Description', link='Link', antiUnaryClause='antiunary')
        rss.addObserver(observer)

        consume(rss.handleRequest(RequestURI='/?query='))

        self.assertEqual(['executeQuery'], [m.name for m in observer.calledMethods])
        self.assertEqual(None, observer.calledMethods[0].kwargs['sortKeys'])
        self.assertEqual(0, observer.calledMethods[0].kwargs['start'])
        self.assertEqual(10, observer.calledMethods[0].kwargs['stop'])
        self.assertEqual(cqlToExpression("antiunary"), observer.calledMethods[0].kwargs['query'])

    def testWebQueryUsesFilters(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        def executeQuery(**kwargs):
            return Response(total=0, hits=[])
            yield
        observer.methods['executeQuery'] = executeQuery
        rss = Rss(title = 'Title', description = 'Description', link = 'Link')
        rss.addObserver(observer)

        consume(rss.handleRequest(RequestURI='/?query=one+two&filter=field1:value1&filter=field2:value2'))
        self.assertEqual(['executeQuery'], [m.name for m in observer.calledMethods])
        self.assertEqual(None, observer.calledMethods[0].kwargs['sortKeys'])
        self.assertEqual(0, observer.calledMethods[0].kwargs['start'])
        self.assertEqual(10, observer.calledMethods[0].kwargs['stop'])
        self.assertEqual(cqlToExpression("(one AND two) AND field1 exact value1 AND field2 exact value2"), observer.calledMethods[0].kwargs['query'])

    def testWebQueryIgnoresWrongFilters(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        observer.exceptions['executeQuery'] = StopIteration([0, []])
        observer.returnValues['executeQuery'] = [0, []]
        rss = Rss(title = 'Title', description = 'Description', link = 'Link')
        rss.addObserver(observer)

        result = "".join(rss.handleRequest(RequestURI='/?query=one+two&filter=invalid&filter='))

        self.assertTrue("<description>An error occurred 'Invalid filter: invalid'</description>" in result, result)
