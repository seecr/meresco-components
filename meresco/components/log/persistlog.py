## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015-2016 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015-2017, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from os import makedirs, stat, rename, listdir, remove
from os.path import isdir, join, isfile
from time import time
import re
from subprocess import Popen
from threading import Thread

from meresco.core import Observable
from meresco.components.json import JsonDict


TEN_MB = 10 * 1024 * 1024
MAX_FILES = 50
MIN_FILES = 3

class PersistLog(Observable):
    def __init__(self, directory, dictToLine=None, maxSize=TEN_MB, maxFiles=MAX_FILES, flush=False, **kwargs):
        Observable.__init__(self, **kwargs)
        self._directory = directory
        isdir(self._directory) or makedirs(self._directory)
        self._dictToLine = dictToLine or (lambda d: JsonDict(d).dumps())
        self._maxSize = maxSize
        self._maxFiles = maxFiles
        if self._maxFiles is not None and self._maxFiles < MIN_FILES:
            raise ValueError("Max files should be at least {0}.".format(MIN_FILES))
        self._currentFilename = join(self._directory, 'current')
        self._currentFile = None
        self._flush = (lambda: self._currentFile.flush()) if flush else (lambda: None)
        self._rotating = False

    def logData(self, dataDict):
        self.writeLogline(self._dictToLine(dataDict))
        return
        yield

    def writeLogline(self, logline):
        self._checkCurrentFile()
        self._currentFile.write(logline+'\n')
        self._size += len(logline) + 1
        self._flush()

    def _checkCurrentFile(self):
        if self._currentFile is None:
            self._size = stat(self._currentFilename).st_size if isfile(self._currentFilename) else 0
        self._sizeCheck()
        if self._currentFile is None:
            self._currentFile = open(self._currentFilename, 'a')

    def _sizeCheck(self):
        if self._size > self._maxSize:
            self.close()
            rename(self._currentFilename, join(self._directory, str(int(time()*1000000))))
            self._size = 0
            self._rotate()

    def _rotate(self):
        if self._rotating:
            return
        self._rotating = True
        def do():
            toBeRotated = sorted([f for f in listdir(self._directory) if filenamesRE.match(f)])[:-1]
            try:
                if not toBeRotated:
                    return
                Popen(['gzip'] + toBeRotated, cwd=self._directory).wait()

                if self._maxFiles:
                    toBeRemoved = sorted([f for f in listdir(self._directory) if filenamesGzRE.match(f)], reverse=True)[self._maxFiles-2:]
                    for f in toBeRemoved:
                        remove(join(self._directory, f))
            finally:
                self._rotating = False
        self._thread = Thread(target=do)
        self._thread.setDaemon(True)
        self._thread.start()

    def commit(self):
        if self._currentFile is None:
            return
        self._currentFile.flush()

    def close(self):
        if self._currentFile is None:
            return
        f, self._currentFile = self._currentFile, None
        f.close()

    def handleShutdown(self):
        print('handle shutdown: saving PersistLog %s' % self._directory)
        from sys import stdout; stdout.flush()
        self.close()


filenamesRE = re.compile(r'^\d{16}$')
filenamesGzRE = re.compile(r'^\d{16}\.gz$')
