## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2016, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2016, 2020 Stichting Kennisnet https://www.kennisnet.nl
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

from seecr.test import SeecrTestCase
from meresco.components.log import LogLine

class LogLineTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.default = LogLine.createDefault()

    def testDefault(self):
        self.assertEqual('2009-11-02T11:25:36Z 11.22.33.44 1.1K 1.300s 42hits /path query=arguments\n',
            self.default(dict(
                timestamp=1257161136.0,
                size=1.1,
                path='/path',
                ipAddress='11.22.33.44',
                duration=1.3,
                queryArguments='query=arguments',
                numberOfRecords=42,
                status="200"
            ))
        )

    def testLogWithLessArguments(self):
        self.assertEqual('2009-11-02T11:25:36Z - - - - - \n',
            self.default(dict(
                timestamp=1257161136.0,
            ))
        )

    def testLogMethod(self):
        self.assertEqual('2009-11-02T11:25:36Z - - - - - \n',
            self.default.log(dict(
                timestamp=1257161136.0,
            ))
        )

    def testCustom(self):
        logline = LogLine('duration', 'timestamp', 'status')
        self.assertEqual('1.300s 2009-11-02T11:25:36Z 200\n',
            logline(dict(
                timestamp=1257161136.0,
                size=1.1,
                path='/path',
                ipAddress='11.22.33.44',
                duration=1.3,
                queryArguments='query=arguments',
                numberOfRecords=42,
                status="200"
            ))
        )

