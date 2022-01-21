## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012, 2016, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2016 SURFmarket https://surf.nl
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

from pylru import lrucache
import pickle
from os import rename
from os.path import isfile

from .timeddictionary import TimedDictionary

class TimedPersistentDictionary(TimedDictionary):
    def __init__(self, timeout, filename, lruMaxSize=None, saveHook=None, loadHook=None):
        TimedDictionary.__init__(self, timeout, lruMaxSize=lruMaxSize)

        self._saveHook = saveHook
        self._loadHook = loadHook
        self._filename = filename
        if isfile(self._filename):
            self._load()

    def __setitem__(self, key, value):
        TimedDictionary.__setitem__(self, key, value)
        self._save()

    def __delitem__(self, key):
        TimedDictionary.__delitem__(self, key)
        self._save()

    def clear(self):
        TimedDictionary.clear(self)
        self._save()

    def purge(self):
        TimedDictionary.purge(self)
        self._save()

    def _save(self):
        dictToStore = self._dictionary if self._saveHook is None else {k:self._saveHook(v) for k,v in self._dictionary.items()}
        fname = self._filename + "~"
        with open(fname, "wb") as f:
            pickle.dump(
                dict(
                    _uuid=self._uuid,
                    _dictionary=dictToStore,
                    _times=self._times,
                    _expirationOrder=self._expirationOrder),
                f)
        rename(fname, self._filename)

    def _load(self):
        with open(self._filename, "rb") as f:
            data = pickle.load(f)
            dictToLoad = data['_dictionary'] if self._loadHook is None else {k:self._loadHook(v) for k,v in data['_dictionary'].items()}
            self._uuid = data['_uuid']
            self._dictionary = dictToLoad
            self._expirationOrder = data['_expirationOrder']
            self._times = data['_times']
