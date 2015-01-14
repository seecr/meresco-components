## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2005-2009 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os.path import join
from os import rename

from seecr.test import SeecrTestCase
from meresco.components import DirectoryWatcher, DirectoryWatcherException

class DirectoryWatcherTest(SeecrTestCase):

    def testNoMask(self):
        try:
            dw = DirectoryWatcher(self.tempdir, lambda f: None)
            self.fail()
        except DirectoryWatcherException as e:
            self.assertEqual('No mask provided.', str(e))

    def testNotifyOnCreateFile(self):
        changedFiles = []
        dw = DirectoryWatcher(self.tempdir, lambda f: changedFiles.append(f), CreateFile=True)
        with open(join(self.tempdir, 'createtest'), 'w') as f:
            f.write("test")
        dw()
        self.assertEqual(1, len(changedFiles))
        self.assertEqual('createtest', changedFiles[0].name)

    def testNotifyOnModifyFile(self):
        changedFiles = []
        with open(join(self.tempdir, 'modifytest'), 'w') as f:
            f.write("line 1")

        dw = DirectoryWatcher(self.tempdir, lambda f: changedFiles.append(f), ModifyFile=True)
        with open(join(self.tempdir, 'modifytest'), 'a') as f:
            f.write("line 2")

        dw()
        self.assertEqual(1, len(changedFiles))
        self.assertEqual('modifytest', changedFiles[0].name)

    def testNotifyOnMoveInFile(self):
        with open('/tmp/tempfile', 'w') as f:
            f.write("test")
        changedFiles = []
        dw = DirectoryWatcher(self.tempdir, lambda f: changedFiles.append(f), MoveInFile=True)

        rename('/tmp/tempfile', join(self.tempdir, 'moveintest'))
        dw()
        self.assertEqual(1, len(changedFiles))
        self.assertEqual('moveintest', changedFiles[0].name)

    def testNotifyOnCreateAndModifyFile(self):
        changedFiles = []
        dw = DirectoryWatcher(self.tempdir, lambda f: changedFiles.append(f), CreateFile=True, ModifyFile=True)
        with open(join(self.tempdir, 'createmodifytest'), 'w') as f:
            pass
        
        dw()
        self.assertEqual(1, len(changedFiles))
        self.assertEqual('createmodifytest', changedFiles[0].name)

        with open(join(self.tempdir, 'createmodifytest'), 'a') as f:
            f.write('test')
        dw()
        self.assertEqual(2, len(changedFiles))
        self.assertEqual('createmodifytest', changedFiles[1].name)
