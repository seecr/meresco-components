## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012-2014, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
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

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import be, consume

from meresco.core import Observable

from meresco.components.sru.srulimitstartrecord import SruLimitStartRecord
from meresco.components.sru import SruException
from meresco.components.sru.diagnostic import UNSUPPORTED_PARAMETER_VALUE

class SruLimitStartRecordTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)

        self.sruLimit = SruLimitStartRecord(limitBeyond=1000)
        def searchRetrieve(**kwargs):
            yield '<result/>'
        self.observer = CallTrace('Observer', methods={'searchRetrieve': searchRetrieve})
        self.dna = be(
            (Observable(),
                (self.sruLimit,
                    (self.observer,)
                )
            )
        )

    def testShouldNotChangeCallsWithStartRecordLowerThanOrEqualTo1000(self):
        sruArguments=dict(
                version='1.1', recordSchema='schema', recordPacking='xml',
                startRecord=1, maximumRecords=10, query='query')
        consume(self.dna.all.searchRetrieve(
            sruArguments=sruArguments,
            otherKwarg="otherKwarg",
            **sruArguments))
        self.assertEqual(['searchRetrieve'], self.observer.calledMethodNames())
        self.assertDictEquals({
                'sruArguments': {
                    'recordSchema': 'schema',
                    'version': '1.1',
                    'recordPacking': 'xml',
                    'maximumRecords': 10,
                    'startRecord': 1,
                    'query': 'query',
                    },
                'otherKwarg': 'otherKwarg',
                'limitBeyond': 1000,
                'recordSchema': 'schema',
                'version': '1.1',
                'recordPacking': 'xml',
                'maximumRecords': 10,
                'startRecord': 1,
                'query': 'query',
            }, self.observer.calledMethods[0].kwargs)

    def testRaiseSruExceptionOnStartRecordAndMaximumRecordTooHigh(self):
        sruArguments=dict(
                version='1.1', recordSchema='schema', recordPacking='xml',
                startRecord=1000, maximumRecords=10, query='query')
        try:
            consume(self.dna.all.searchRetrieve(sruArguments=sruArguments, **sruArguments))
            self.fail()
        except SruException as e:
            self.assertEqual(UNSUPPORTED_PARAMETER_VALUE[0], e.code)
            self.assertEqual(UNSUPPORTED_PARAMETER_VALUE[1], e.message)
            self.assertEqual("Argument 'startRecord' and 'maximumRecords' too high, maximum: 1000", e.details)


    def testShouldRewriteRequestOnStartRecordMoreThan1000(self):
        sruArguments=dict(
                version='1.1', recordSchema='schema', recordPacking='xml',
                startRecord=1001, maximumRecords=10, query='query')
        try:
            consume(self.dna.all.searchRetrieve(sruArguments=sruArguments, **sruArguments))
            self.fail()
        except SruException as e:
            self.assertEqual(UNSUPPORTED_PARAMETER_VALUE[0], e.code)
            self.assertEqual(UNSUPPORTED_PARAMETER_VALUE[1], e.message)
            self.assertEqual("Argument 'startRecord' too high, maximum: 1000", e.details)
