## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

from cq2utils import CQ2TestCase, CallTrace
from amara.binderytools import bind_string
from urllib import urlencode

from meresco.components.facetindex import Response
from meresco.components.rss import Rss

from cqlparser import parseString as parseCql

RSS_HEAD = """HTTP/1.0 200 OK
Content-Type: application/rss+xml

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

class RssTest(CQ2TestCase):

    def testNoResults(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        observer.exceptions['executeQuery'] = StopIteration(Response(total=0, hits=[]))

        rss = Rss(
            title = 'Test title',
            description = 'Test description',
            link = 'http://www.example.org',
            sortKeys = 'date,,1',
            maximumRecords = '15',
        )
        rss.addObserver(observer)

        result = "".join(list(rss.handleRequest(RequestURI='/?query=aQuery')))
        self.assertEqualsWS(RSS % '', result)

    def testOneResult(self):
        observer = CallTrace(
            methods={
                'getRecord': lambda recordId: (g for g in ['<item><title>Test Title</title><link>Test Identifier</link><description>Test Description</description></item>']),
            },
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        observer.exceptions['executeQuery'] = StopIteration(Response(total=1, hits=[1]))

        rss = Rss(
            title = 'Test title',
            description = 'Test description',
            link = 'http://www.example.org',
            sortKeys = 'date,,1',
            maximumRecords = '15',
        )
        rss.addObserver(observer)

        result = "".join(list(rss.handleRequest(RequestURI='/?query=aQuery')))
        self.assertEqualsWS(RSS % """<item>
        <title>Test Title</title>
        <link>Test Identifier</link>
        <description>Test Description</description>
        </item>""", result)

    def testError(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        observer.exceptions['executeQuery'] = StopIteration(Response(total=0, hits=[]))
        rss = Rss(
            title = 'Test title',
            description = 'Test description',
            link = 'http://www.example.org',
        )
        rss.addObserver(observer)
        result = "".join(list(rss.handleRequest(RequestURI='/?query=aQuery%29'))) #%29 == ')'

        xml = bind_string(result[result.index("<?xml"):])
        self.assertEquals('Test title', str(xml.rss.channel.title))
        self.assertFalse('''An error occurred 'Unexpected token after parsing''' in str(xml.rss.channel.description), str(xml.rss.channel.description))

    def testErrorNoQuery(self):
        rss = Rss(
            title = 'Test title',
            description = 'Test description',
            link = 'http://www.example.org',
        )
        result = "".join(list(rss.handleRequest(RequestURI='/')))

        xml = bind_string(result[result.index("<?xml"):])
        self.assertEquals('ERROR Test title', str(xml.rss.channel.title))
        self.assertTrue('''An error occurred 'MANDATORY parameter 'query' not supplied or empty''' in str(xml.rss.channel.description), str(xml.rss.channel.description))


    def assertMaxAndSort(self, maximumRecords, sortKey, sortDirection, rssArgs, sruArgs):
        rss = Rss(
            title = 'Test title',
            description = 'Test description',
            link = 'http://www.example.org',
            **rssArgs
        )
        recordIds = []
        def getRecord(recordId):
            recordIds.append(recordId)
            return '<item/>'

        def executeQuery(start, stop, *args, **kwargs):
            response = Response(total=50, hits=range(start, stop))
            raise StopIteration(response)
        observer = CallTrace(
            methods={
                'executeQuery': executeQuery,
                'getRecord': getRecord,
            },
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        rss.addObserver(observer)

        result = "".join(list(rss.handleRequest(RequestURI='/?query=aQuery&' + urlencode(sruArgs))))

        method = observer.calledMethods[0]
        self.assertEquals('executeQuery', method.name)
        self.assertEquals(sortKey, method.kwargs['sortBy'])
        self.assertEquals(sortDirection, method.kwargs['sortDescending'])
        self.assertEquals(maximumRecords, len(recordIds))

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
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        rss = Rss(title = 'Title', description = 'Description', link = 'Link')
        rss.addObserver(observer)

        result = "".join(rss.handleRequest())
        self.assertTrue('Content-Type: application/rss+xml' in result, result)

    def testWebQueryUsage(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        observer.exceptions['executeQuery'] = StopIteration(Response(total=0, hits=[]))
        rss = Rss(title = 'Title', description = 'Description', link = 'Link')
        rss.addObserver(observer)

        result = "".join(rss.handleRequest(RequestURI='/?query=one+two'))
        self.assertEquals(["executeQuery(stop=10, cqlAbstractSyntaxTree=<class CQL_QUERY>, sortDescending=None, sortBy=None, start=0)"], [str(m) for m in observer.calledMethods])

    def testAntiUnaryClauseIsPassedToWebQuery(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        observer.exceptions['executeQuery'] = StopIteration(Response(total=0, hits=[]))
        rss = Rss(title='Title', description='Description', link='Link', antiUnaryClause='antiunary')
        rss.addObserver(observer)

        result = "".join(rss.handleRequest(RequestURI='/?query=not+fiets'))
        
        self.assertEquals(["executeQuery(stop=10, cqlAbstractSyntaxTree=<class CQL_QUERY>, sortDescending=None, sortBy=None, start=0)"], [str(m) for m in observer.calledMethods])
        self.assertCql(parseCql("antiunary NOT fiets"), observer.calledMethods[0].kwargs['cqlAbstractSyntaxTree'])

    def testWebQueryUsesFilters(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        observer.exceptions['executeQuery'] = StopIteration(Response(total=0, hits=[]))
        rss = Rss(title = 'Title', description = 'Description', link = 'Link')
        rss.addObserver(observer)

        result = "".join(rss.handleRequest(RequestURI='/?query=one+two&filter=field1:value1&filter=field2:value2'))
        self.assertEquals(["executeQuery(stop=10, cqlAbstractSyntaxTree=<class CQL_QUERY>, sortDescending=None, sortBy=None, start=0)"], [str(m) for m in observer.calledMethods])

        self.assertCql(parseCql("(one AND two) AND field1 exact value1 AND field2 exact value2"), observer.calledMethods[0].kwargs['cqlAbstractSyntaxTree'])

    def testWebQueryIgnoresWrongFilters(self):
        observer = CallTrace(
            ignoredAttributes=['unknown', 'extraResponseData', 'echoedExtraRequestData'])
        observer.exceptions['executeQuery'] = StopIteration([0, []])
        rss = Rss(title = 'Title', description = 'Description', link = 'Link')
        rss.addObserver(observer)

        result = "".join(rss.handleRequest(RequestURI='/?query=one+two&filter=invalid&filter='))

        self.assertTrue("<description>An error occurred 'Invalid filter: invalid'</description>" in result, result)

    def assertCql(self, expected, input):
        self.assertEquals(expected, input, '%s != %s' %(expected.prettyPrint(), input.prettyPrint()))
