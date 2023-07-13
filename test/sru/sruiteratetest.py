## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2019-2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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
from io import BytesIO
from urllib.parse import urlparse, parse_qs

from meresco.components.sru.sruiterate import iterateSruQuery, SruQuery

class SruIterateTest(SeecrTestCase):
    def testIterate(self):
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
        self.assertEqual(2, len([each.data for each in sruResult])) # check to make sure getting the data works)
        self.assertTrue(2, parse_qs(urlparse(requestedUrls[1]).query)['startRecord'][0])

    def testFromUrl(self):
        sruQuery = SruQuery.fromUrl("https://hostname:port/path?query=aap&recordSchema=something")
        self.assertEqual("https://hostname:port/path", sruQuery._baseUrl)
        self.assertEqual("aap", sruQuery._query)
        self.assertEqual("something", sruQuery._recordSchema)
        self.assertEqual("xml", sruQuery._recordPacking)

        sruQuery = SruQuery.fromUrl("https://hostname:port/path?query=aap", recordSchema="something")
        self.assertEqual("https://hostname:port/path", sruQuery._baseUrl)
        self.assertEqual("aap", sruQuery._query)
        self.assertEqual("something", sruQuery._recordSchema)
        self.assertEqual("xml", sruQuery._recordPacking)

        sruQuery = SruQuery.fromUrl("https://hostname:port/path?query=aap", recordSchema="something", recordPacking="json")
        self.assertEqual("https://hostname:port/path", sruQuery._baseUrl)
        self.assertEqual("aap", sruQuery._query)
        self.assertEqual("something", sruQuery._recordSchema)
        self.assertEqual("json", sruQuery._recordPacking)

        try:
            sruQuery = SruQuery.fromUrl("https://hostname:port/path")
            self.fail()
        except ValueError as e:
            self.assertEqual("No query specified", str(e))

        try:
            sruQuery = SruQuery.fromUrl("https://hostname:port/path?query=aap")
            self.fail()
        except ValueError as e:
            self.assertEqual("No recordSchema specified", str(e))

    def testIterateWithEncodingIssue(self):
        responses = [
            response(
                numberOfRecords=1,
                records=[dict(
                    identifier="ID-1",
                    data=ENCODING_ISSUE_RECORD)]),
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

        self.assertEqual(1, len(sruResult))
        self.assertEqual(1, len(requestedUrls))
        self.assertEqual(['ID-1'], [each.identifier for each in sruResult])
        self.assertEqual(1, len([each.data for each in sruResult])) # check to make sure getting the data works)
        self.assertTrue(1, parse_qs(urlparse(requestedUrls[0]).query)['startRecord'][0])

def response(numberOfRecords, records, nextRecordPosition=None):

    def record(identifier, data, packing="xml"):
        return """
<srw:record>
    <srw:recordSchema>richrecord</srw:recordSchema>
    <srw:recordPacking>{packing}</srw:recordPacking>
    <srw:recordIdentifier>{identifier}</srw:recordIdentifier>
    <srw:recordData>{data}</srw:recordData>
</srw:record>""".format(packing=packing, identifier=identifier, data=data)

    _response = """<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:meresco_srw="http://meresco.org/namespace/srw#">
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
    nextRecordPositionTag="<srw:nextRecordPosition>{}</srw:nextRecordPosition>".format(nextRecordPosition) if nextRecordPosition else '')

    return BytesIO(bytes(_response, encoding="utf-8"))


ENCODING_ISSUE_RECORD = """<didl:DIDL xmlns:didl="urn:mpeg:mpeg21:2002:02-DIDL-NS" xmlns:mods="http://www.loc.gov/mods/v3" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dii="urn:mpeg:mpeg21:2002:01-DII-NS" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dai="info:eu-repo/dai" xmlns:diext="http://library.lanl.gov/2004-04/STB-RL/DIEXT" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:doc="http://www.lyncode.com/xoai" xmlns:xalan="http://xml.apache.org/xalan" xmlns="http://www.openarchives.org/OAI/2.0/" xsi:schemaLocation="urn:mpeg:mpeg21:2002:02-DIDL-NS http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/did/didl.xsd urn:mpeg:mpeg21:2002:01-DII-NS http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/dii/dii.xsd http://purl.org/dc/terms/ http://dublincore.org/schemas/xmls/qdc/dcterms.xsd" DIDLDocumentId="urn:nbn:nl:hs:25-20.500.12470/2372">
    <!--Top level Item-->
    <didl:Item>
        <didl:Descriptor>
            <didl:Statement mimeType="application/xml">
                <dii:Identifier>urn:nbn:nl:hs:25-20.500.12470/2372</dii:Identifier>
            </didl:Statement>
        </didl:Descriptor>
        <didl:Descriptor>
            <didl:Statement mimeType="application/xml">
                <dcterms:modified>2021-12-22T20:00:03.772351Z</dcterms:modified>
            </didl:Statement>
        </didl:Descriptor>
        <didl:Component>
            <didl:Resource mimeType="application/xml" ref="http://hdl.handle.net/20.500.12470/2372"/>
        </didl:Component>
        <!--Introducing MODS metadata-->
        <didl:Item>
            <didl:Descriptor>
                <!--ObjectType of Item-->
                <didl:Statement mimeType="application/xml">
                    <rdf:type rdf:resource="info:eu-repo/semantics/descriptiveMetadata"/>
                </didl:Statement>
            </didl:Descriptor>
            <didl:Component>
                <didl:Resource mimeType="application/xml">
                            <mods xmlns="http://www.loc.gov/mods/v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="3.6" xsi:schemaLocation="http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods-3-6.xsd">
                                <!--0 Position : 1--><mods:name type="personal" ID="n2372_aut_en_US_1">
                        <mods:namePart type="family">Jonvik</mods:namePart>
                        <mods:namePart type="given">K.L.</mods:namePart>
                        <mods:displayForm>Jonvik, K.L.</mods:displayForm>
                        <mods:role>
                            <mods:roleTerm type="code" authority="marcrelator">aut</mods:roleTerm>
                            <mods:roleTerm type="text" authority="marcrelator">Author</mods:roleTerm>
                        </mods:role>
                    </mods:name>
                    <!--0 Position : 2-->
                    <mods:name type="personal" ID="n2372_aut_en_US_2">
                        <mods:namePart type="family">Hoogervorst</mods:namePart>
                        <mods:namePart type="given">D.</mods:namePart>
                        <mods:displayForm>Hoogervorst, D.</mods:displayForm>
                        <mods:role>
                            <mods:roleTerm type="code" authority="marcrelator">aut</mods:roleTerm>
                            <mods:roleTerm type="text" authority="marcrelator">Author</mods:roleTerm>
                        </mods:role>
                    </mods:name>
                    <!--0 Position : 3-->
                    <mods:name type="personal" ID="n2372_aut_en_US_3">
                        <mods:namePart type="family">Peelen</mods:namePart>
                        <mods:namePart type="given">H.B.</mods:namePart>
                        <mods:displayForm>Peelen, H.B.</mods:displayForm>
                        <mods:role>
                            <mods:roleTerm type="code" authority="marcrelator">aut</mods:roleTerm>
                            <mods:roleTerm type="text" authority="marcrelator">Author</mods:roleTerm>
                        </mods:role>
                    </mods:name>
                    <!--0 Position : 4-->
                    <mods:name type="personal" ID="n2372_aut_en_US_4">
                        <mods:namePart type="family">Niet</mods:namePart>
                        <mods:namePart type="given">M. de</mods:namePart>
                        <mods:displayForm>Niet, M. de</mods:displayForm>
                        <mods:role>
                            <mods:roleTerm type="code" authority="marcrelator">aut</mods:roleTerm>
                            <mods:roleTerm type="text" authority="marcrelator">Author</mods:roleTerm>
                        </mods:role>
                        <mods:nameIdentifier typeURI="info:eu-repo/dai/nl" type="dai-nl">31465836X</mods:nameIdentifier>
                    </mods:name>
                    <!--0 Position : 7-->
                    <mods:name type="personal" ID="n2372_aut_en_US_5">
                        <mods:namePart type="family">Verdijk</mods:namePart>
                        <mods:namePart type="given">L.B.</mods:namePart>
                        <mods:displayForm>Verdijk, L.B.</mods:displayForm>
                        <mods:role>
                            <mods:roleTerm type="code" authority="marcrelator">aut</mods:roleTerm>
                            <mods:roleTerm type="text" authority="marcrelator">Author</mods:roleTerm>
                        </mods:role>
                    </mods:name>
                    <!--0 Position : 8-->
                    <mods:name type="personal" ID="n2372_aut_en_US_6">
                        <mods:namePart type="family">Loon</mods:namePart>
                        <mods:namePart type="given">L.J.C. van</mods:namePart>
                        <mods:displayForm>Loon, L.J.C. van</mods:displayForm>
                        <mods:role>
                            <mods:roleTerm type="code" authority="marcrelator">aut</mods:roleTerm>
                            <mods:roleTerm type="text" authority="marcrelator">Author</mods:roleTerm>
                        </mods:role>
                        <mods:nameIdentifier typeURI="info:eu-repo/dai/nl" type="dai-nl">322064570</mods:nameIdentifier>
                    </mods:name>
                    <!--0 Position : 11-->
                    <mods:name type="personal" ID="n2372_aut_en_US_7">
                        <mods:namePart type="family">Dijk</mods:namePart>
                        <mods:namePart type="given">J.W. van</mods:namePart>
                        <mods:displayForm>Dijk, J.W. van</mods:displayForm>
                        <mods:role>
                            <mods:roleTerm type="code" authority="marcrelator">aut</mods:roleTerm>
                            <mods:roleTerm type="text" authority="marcrelator">Author</mods:roleTerm>
                        </mods:role>
                    </mods:name>
                    <mods:abstract>Purpose: Dietary nitrate has been shown to enhance muscle contractile function and has, therefore, been linked to increased muscle power and sprint exercise performance. However, the impact of dietary nitrate supplementation on maximal strength, performance and muscular endurance remains to be established. Methods: Fifteen recreationally active males (25 &#177;4 y, BMI 24 &#177;3 kg/m(2)) participated in a randomized double-blinded cross-over study comprising two 6-d supplementation periods; 140 mL/d nitrate-rich (BR; 985 mg/d) and nitrate-depleted (PLA; 0.37 mg/d) beetroot juice. Three hours following the last supplement, we assessed countermovement jump (CMJ) performance, maximal strength and power of the upper leg by voluntary isometric (30&#176; and 60&#176; angle) and isokinetic contractions (60, 120, 180 and 300&#176;&#8226;s(-1)), and muscular endurance (total workload) by 30 reciprocal isokinetic voluntary contractions at 180&#176;&#8226;s(-1). Results: Despite differences in plasma nitrate (BR: 879 &#177;239 vs. PLA: 33 &#177;13 &#956;mol/L, Pn&amp;lt;n0.001) and nitrite (BR: 463 &#177;217 vs. PLA: 176 &#177;50 nmol/L, Pn&amp;lt;n0.001) concentrations prior to exercise testing, CMJ height (BR: 39.3 &#177;6.3 vs. PLA: 39.6 &#177;6.3 cm; Pn=n0.39) and muscular endurance (BR: 3.93 &#177;0.69 vs. PLA: 3.90 &#177;0.66 kJ; Pn=n0.74) were not different between treatments. In line, isometric strength (Pn&amp;gt;n0.50 for both angles) and isokinetic knee extension power (Pn&amp;gt;n0.33 for all velocities) did not differ between treatments. Isokinetic knee flexion power was significantly higher following BR compared with PLA ingestion at 60&#176;&#8226;s(-1) (Pn=n0.001), but not at 120&#176;&#8226;s(-1) (Pn=n0.24), 180&#176;&#8226;s(-1) (Pn=n0.066), and 300&#176;&#8226;s(-1) (Pn=n0.36). Conclusion: Nitrate supplementation does not improve maximal strength, countermovement jump performance and muscular endurance in healthy, active males.</mods:abstract>
                                </mods>
                            </didl:Resource>
            </didl:Component>
        </didl:Item>
    </didl:Item>
</didl:DIDL>"""
