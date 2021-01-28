## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014, 2016, 2018, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2014, 2020 Stichting Kennisnet https://www.kennisnet.nl
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

from io import StringIO

from seecr.test import SeecrTestCase

from meresco.components.log import ApacheLogWriter
from meresco.components.log.utils import getScoped


class ApacheLogWriterTest(SeecrTestCase):
    def testNormalLog(self):
        stream = StringIO()
        writer = ApacheLogWriter(stream)
        writer.writeLog(
            collectedLog={
                'httpRequest': {
                    'Headers': [{}],
                    'Client': [('10.11.12.13', 12345)],
                    'timestamp': [1468845136.824253],
                    'Method': ['GET'],
                    'RequestURI': ['/abc'],
                },
                'httpResponse': {
                    'httpStatus': ['200'],
                }
            }
        )
        self.assertEqual('10.11.12.13 - - [18/Jul/2016:12:32:16 +0000] "GET /abc HTTP/1.0" 200 - "-" "-"\n', stream.getvalue())

    def testLogWithException(self):
        stream = StringIO()
        writer = ApacheLogWriter(stream)
        writer.writeLog(
            collectedLog={
                'httpRequest': {
                    'Headers': [{}],
                    'Client': [('10.11.12.13', 12345)],
                    'timestamp': [1468845136.824253],
                    'Method': ['GET'],
                    'RequestURI': ['/abc'],
                },
                'httpResponse': {
                    'httpStatus': ['200'],
                    'exception': [ValueError('xyz')]
                }
            }
        )
        self.assertEqual('10.11.12.13 - - [18/Jul/2016:12:32:16 +0000] "GET /abc HTTP/1.0" 200 - "-" "-" Exception raised:\n    ValueError(\'xyz\')\n', stream.getvalue())

    def testWriteLogWithoutSensibleData(self):
        stream = StringIO()
        writer = ApacheLogWriter(stream)
        writer.writeLog(collectedLog={'key':['value']})
        self.assertEqual("", stream.getvalue())

    def testRejectLog(self):
        stream = StringIO()
        writer = ApacheLogWriter(stream, rejectLog=lambda collectedLog: getScoped(collectedLog, scopeNames=(), key='httpRequest').get('RequestURI') == ['/abc'])
        collectedLog={
            'httpRequest': {
                'Headers': [{}],
                'Client': [('10.11.12.13', 12345)],
                'timestamp': [1468845136.824253],
                'Method': ['GET'],
                'RequestURI': ['/abc'],
            },
            'httpResponse': {
                'httpStatus': ['200'],
            }
        }
        writer.writeLog(collectedLog)
        self.assertEqual('', stream.getvalue())
        collectedLog['httpRequest']['RequestURI'] = ['/abcd']
        writer.writeLog(collectedLog)
        self.assertEqual('10.11.12.13 - - [18/Jul/2016:12:32:16 +0000] "GET /abcd HTTP/1.0" 200 - "-" "-"\n', stream.getvalue())
