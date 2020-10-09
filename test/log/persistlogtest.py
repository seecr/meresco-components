## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015-2016 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015-2017 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os import listdir
from os.path import join
import gzip

from seecr.test import SeecrTestCase

from weightless.core import consume

from meresco.components.log import PersistLog
from meresco.components.log.packettolog import dictToLogline


class PersistLogTest(SeecrTestCase):
    def testLogData(self):
        persist = PersistLog(join(self.tempdir, 'store'), dictToLine=dictToLogline)
        consume(persist.logData(dataDict=LOGDATADICT))
        persist.close()
        with open(join(self.tempdir, 'store', 'current')) as fp:
            self.assertEqual(
                '2009-11-02T11:25:36Z 11.12.13.14 4.0K 12.340s 0hits /path key=value\n', fp.read())

    def testMaxFileSize(self):
        with open(join(self.tempdir, 'current'), 'w') as f:
            f.write('2008-11-02T11:25:36Z 11.12.13.14 4.0K 12.340s 0hits /path key=value\n')
        persist = PersistLog(self.tempdir, maxSize=10, dictToLine=dictToLogline)
        try:
            consume(persist.logData(dataDict=LOGDATADICT))
            persist.close()

            with open(join(self.tempdir, 'current')) as fp:
                self.assertEqual(
                    '2009-11-02T11:25:36Z 11.12.13.14 4.0K 12.340s 0hits /path key=value\n',
                    fp.read())
            self.assertEqual(2 , len(listdir(self.tempdir)))
            consume(persist.logData(dataDict=LOGDATADICT))
            consume(persist.logData(dataDict=LOGDATADICT))
            persist._thread.join()
            consume(persist.logData(dataDict=LOGDATADICT))
            persist._thread.join()
            self.assertEqual(5, len(listdir(self.tempdir)))
            self.assertTrue('current' in listdir(self.tempdir))
            self.assertEqual(3, len([l for l in listdir(self.tempdir) if l.endswith('.gz')]))
        finally:
            persist.close()

    def testMaxFiles(self):
        self.assertRaises(ValueError, lambda: PersistLog(self.tempdir, maxSize=10, maxFiles=2))
        persist = PersistLog(self.tempdir, maxSize=10, maxFiles=3)
        def dataDict(nr):
            d = LOGDATADICT.copy()
            d['arguments'] += '&line=%s' % nr
            return d
        consume(persist.logData(dataDict=dataDict(1)))
        self.assertEqual(1, len(listdir(self.tempdir)))
        consume(persist.logData(dataDict=dataDict(2)))
        persist._thread.join()
        self.assertEqual(2, len(listdir(self.tempdir)))
        consume(persist.logData(dataDict=dataDict(3)))
        persist._thread.join()
        self.assertEqual(3, len(listdir(self.tempdir)))
        consume(persist.logData(dataDict=dataDict(4)))
        persist._thread.join()
        self.assertEqual(3, len(listdir(self.tempdir)))
        consume(persist.logData(dataDict=dataDict(5)))
        persist._thread.join()
        self.assertEqual(3, len(listdir(self.tempdir)))
        persist.close()
        zipped, notzipped, current = sorted(listdir(self.tempdir))
        self.assertEqual('current', current)
        self.assertTrue(zipped.endswith('.gz'))
        with open(join(self.tempdir, current)) as fp:
            self.assertTrue('line=5' in fp.read())
        with open(join(self.tempdir, notzipped)) as fp:
            self.assertTrue('line=4' in fp.read())
        with gzip.open(join(self.tempdir, zipped)) as fp:
            self.assertTrue(b'line=3' in fp.read())

    def testMaxFilesNoLimit(self):
        PersistLog(self.tempdir, maxSize=10, maxFiles=None)


LOGDATADICT={
    'timestamp': 1257161136,
    'ipAddress': '11.12.13.14',
    'size': 4096,
    'duration': 12340,
    'hits': 0,
    'path': '/path',
    'arguments': 'key=value',
}
