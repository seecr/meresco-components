## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2014 Stichting Kennisnet http://www.kennisnet.nl
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
from meresco.components.log import DirectoryLog
from os import listdir
from os.path import join, isdir
from meresco.components.log.directorylog import NR_OF_FILES_KEPT

class DirectoryLogTest(SeecrTestCase):

    def testMinimalLog(self):
        log = DirectoryLog(self.tempdir)
        log.log(
            timestamp=1257161136.0
            )
        self.assertEqual(['2009-11-02-query.log'], listdir(self.tempdir))
        self.assertEqual('2009-11-02T11:25:36Z - - - - - \n', open(join(self.tempdir, '2009-11-02-query.log')).read())

    def testAppendToLog(self):
        with open(join(self.tempdir, '2009-11-02-query.log'), 'w') as f:
            f.write('line0\n')
        log = DirectoryLog(self.tempdir)
        log.log(**DEFAULT_KWARGS())
        self.assertEqual(['2009-11-02-query.log'], listdir(self.tempdir))
        self.assertEqual('line0\n2009-11-02T11:25:36Z 11.22.33.44 1.1K 1.300s 42hits /path query=arguments\n', open(join(self.tempdir, '2009-11-02-query.log')).read())

    def testNewDayNewLogFile(self):
        kwargs = DEFAULT_KWARGS()
        kwargs['timestamp'] = 1257161136.0
        log = DirectoryLog(self.tempdir)
        log.log(**kwargs)
        kwargs['timestamp'] += 24 * 60 * 60
        log.log(**kwargs)
        self.assertEqual(['2009-11-02-query.log', '2009-11-03-query.log'], sorted(listdir(self.tempdir)))
        self.assertEqual('2009-11-03T11:25:36Z 11.22.33.44 1.1K 1.300s 42hits /path query=arguments\n', open(join(self.tempdir, '2009-11-03-query.log')).read())

    def testLogDirCreated(self):
        logDir = join(self.tempdir, 'amihere')
        self.assertFalse(isdir(logDir))
        DirectoryLog(logDir)
        self.assertTrue(isdir(logDir))

    def testSetExtension(self):
        log = DirectoryLog(self.tempdir, extension='-the-end.log')
        log.log(**DEFAULT_KWARGS())
        self.assertEqual(['2009-11-02-the-end.log'], listdir(self.tempdir))

    def testRemoveOldLogs(self):
        kwargs = DEFAULT_KWARGS()
        kwargs['timestamp'] = 1257161136.0
        for filename in ("%03d" % r for r in range(NR_OF_FILES_KEPT)):
            open(join(self.tempdir, filename), 'w').close()

        filesBefore = listdir(self.tempdir)
        log = DirectoryLog(self.tempdir, extension='-the-end.log')
        log.log(**kwargs)
        filesAfter = listdir(self.tempdir)
        self.assertFalse('000' in filesAfter)
        self.assertEqual(len(filesAfter), len(filesBefore))

        filesBefore = listdir(self.tempdir)
        kwargs['timestamp'] += 3600*24
        log.log(**kwargs)
        filesAfter = listdir(self.tempdir)
        self.assertFalse('001' in filesAfter)
        self.assertEqual(len(filesAfter), len(filesBefore))

        open(join(self.tempdir, '015'), 'w').close()
        open(join(self.tempdir, '016'), 'w').close()
        kwargs['timestamp'] += 3600*24
        log.log(**kwargs)
        self.assertEqual(NR_OF_FILES_KEPT, len(listdir(self.tempdir)))




DEFAULT_KWARGS = lambda: dict(
        timestamp=1257161136.0,
        size=1.1,
        path='/path',
        ipAddress='11.22.33.44',
        duration=1.3,
        queryArguments='query=arguments',
        numberOfRecords=42,
    )
