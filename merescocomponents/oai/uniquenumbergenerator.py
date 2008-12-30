## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
CHUNKSIZE = 1000

import os
from math import floor
from thread import allocate_lock
from shutil import move
from time import sleep

class UniqueNumberGenerator:

        def __init__(self, filename):
                self.filename = filename
                if os.path.exists(filename):
                        self._nr = self._read()
                else:
                        self._nr = -1
                self._reserved = self._nr
                self._lock = allocate_lock()

        def next(self):
                self._lock.acquire()
                try:
                        self._nr += 1
                        assert not sleep(0.000001) # yield current thread (forces tests to fail always if there would not be locking, as opposed to non-deterministic failures)
                        self._reserve(self._nr)
                        result = self._nr
                finally:
                        self._lock.release()
                return result

        def _reserve(self, nr):
                reserved =  int(floor(nr / (1.0 * CHUNKSIZE)) + 1) * CHUNKSIZE
                if reserved > self._reserved:
                        self._write(reserved)
                        self._reserved = reserved

        def _write(self, nr):
                f = open(self.filename + '.atomic', 'w')
                try:
                        f.write(str(nr))
                finally:
                        f.close()
                move(self.filename + '.atomic', self.filename)

        def _read(self):
                f = open(self.filename)
                try:
                        result = int(f.read())
                finally:
                        f.close()
                return result
