## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2019 Seecr (Seek You Too B.V.) https://seecr.nl
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

from seecr.test import SeecrTestCase
from StringIO import StringIO
from urlparse import urlparse, parse_qs

from meresco.components.sru.sruiterate import iterateSruQuery

class SruIterateTest(SeecrTestCase):
    def testOne(self):
        responses = [
            response(
                numberOfRecords=2,
                records=[dict(
                    identifier="ID-1",
                    data="""<lp:woord xmlns:lp="http://leesplankje.nl">aap</lp:woord>""")],
                nextRecordPosition=2),
            response(
                numberOfRecords=2,
                records=[dict(
                    identifier="ID-2",
                    data="""<lp:woord xmlns:lp="http://leesplankje.nl">noot</lp:woord>""")]),
        ]
        
        requestedUrls = []
        def _urlopen(url):
            requestedUrls.append(url)
            return responses.pop(0)

        sruResult = list(iterateSruQuery(
            baseUrl="http://the_base.url",
            query="some query",
            recordSchema="something",
            _urlopen = _urlopen))

        self.assertEqual(2, len(sruResult))
        self.assertEqual(2, len(requestedUrls))
        self.assertEqual(['ID-1', 'ID-2'], [each.identifier for each in sruResult])
        self.assertTrue(2, parse_qs(urlparse(requestedUrls[1]).query)['startRecord'][0])



def response(numberOfRecords, records, nextRecordPosition=None):

    def record(identifier, data, packing="xml"):
        return """
<srw:record>
    <srw:recordSchema>richrecord</srw:recordSchema>
    <srw:recordPacking>{packing}</srw:recordPacking>
    <srw:recordIdentifier>{identifier}</srw:recordIdentifier>
    <srw:recordData>{data}</srw:recordData>
</srw:record>""".format(packing=packing, identifier=identifier, data=data)

    return StringIO("""<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:meresco_srw="http://meresco.org/namespace/srw#">
    <srw:version>1.2</srw:version>
    <srw:numberOfRecords>{numberOfRecords}</srw:numberOfRecords>
    <srw:records>{recordsData}</srw:records>{nextRecordPositionTag}
    <srw:echoedSearchRetrieveRequest>
        <srw:version>1.2</srw:version>
        <srw:query>84aeff65-748d-4040-9175-9d573480b013</srw:query>
        <srw:startRecord>2</srw:startRecord>
        <srw:maximumRecords>1</srw:maximumRecords>
        <srw:recordPacking>xml</srw:recordPacking>
        <srw:recordSchema>richrecord</srw:recordSchema>
    </srw:echoedSearchRetrieveRequest>
    <srw:extraResponseData>
        <querytimes xmlns="http://meresco.org/namespace/timing">
        <sruHandling>PT0.003S</sruHandling>
        <sruQueryTime>PT0.002S</sruQueryTime>
        <index>PT0.000S</index>
        </querytimes>
    </srw:extraResponseData>
</srw:searchRetrieveResponse>""".format(
    numberOfRecords=numberOfRecords,
    recordsData=''.join(record(**each) for each in records),
    nextRecordPositionTag="<srw:nextRecordPosition>{}</srw:nextRecordPosition>".format(nextRecordPosition) if nextRecordPosition else ''))
