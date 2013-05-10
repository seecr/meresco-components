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

from pyinotify import WatchManager, Notifier, EventsCodes

EVENT_MAPPING = {
    'CreateFile': EventsCodes.ALL_FLAGS['IN_CREATE'],
    'ModifyFile': EventsCodes.ALL_FLAGS['IN_MODIFY'],
    'MoveInFile': EventsCodes.ALL_FLAGS['IN_MOVED_TO'],
}

class DirectoryWatcherException(Exception):
    pass

class DirectoryWatcher(object):
    def __init__(self, path, method, **kwargs):
        self._wm = WatchManager()

        mask = 0
        for key in kwargs:
            if key in EVENT_MAPPING and kwargs[key] == True:
                mask = mask | EVENT_MAPPING[key]
        if mask == 0:
            raise  DirectoryWatcherException('No mask provided.')
        self._wm.add_watch(path, mask)
        self._notifier = Notifier(self._wm, method)

    def fileno(self):
        return self._notifier._fd

    def close(self):
        self._notifier.stop()

    def __call__(self):
        self._notifier.read_events()
        self._notifier.process_events()
