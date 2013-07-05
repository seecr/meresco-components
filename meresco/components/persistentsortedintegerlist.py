# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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

from os import remove, rename
from os.path import isfile, basename
from bisect import bisect_left

from integerlist.integerlist import IntegerList


class PersistentSortedIntegerList(object):
    def __init__(self, filepath, mergeTrigger=10000, autoCommit=True):
        self._filepath = filepath
        self.__name = basename(filepath)
        self._deletesFilepath = filepath + '.deleted'
        self._mergeTrigger = mergeTrigger
        self._autoCommit = autoCommit
        self._cleanupInCaseOfCrashDuringMerge()
        self._iList = IntegerList()
        self._deletesList = IntegerList()
        if isfile(self._filepath):
            self._iList.extendFrom(self._filepath)
        if isfile(self._deletesFilepath):
            self._deletesList.extendFrom(self._deletesFilepath)
            for position in self._deletesList:
                del self._iList[position]
            self._merge()
        self._unsavedFromOffset = len(self)
        self._deletesSaved = 0

    def __len__(self):
        return self._iList.__len__()

    def __iter__(self):
        return self._iList.__iter__()

    def __contains__(self, element):
        return self._position(element) != -1

    def __getitem__(self, index):
        return self._iList.__getitem__(index)

    def append(self, element):
        size = len(self)
        if size > 0 and element <= self[-1]:
            raise ValueError("list.append(%d): expected value to be greater than %d" % (element, self[-1]))
        self._iList.append(element)
        if self._autoCommit:
            self.commit()

    def remove(self, element):
        position = self._position(element)
        if position == -1:
            raise ValueError('list.remove(%s): %s not in list' % (element, element))
        del self._iList[position]
        if position < self._unsavedFromOffset:
            self._unsavedFromOffset -= 1
            self._deletesList.append(position)
        if self._autoCommit:
            self.commit()
        if len(self._deletesList) >= self._mergeTrigger:
            self._merge()

    def index(self, item):
        position = self._position(item)
        if position == -1:
            raise ValueError('list.index(%s): %s not in list' % (item, item))
        return position

    def commit(self):
        if self._unsavedFromOffset < len(self):
            self._save(self._iList, self._filepath, offset=self._unsavedFromOffset, append=True)
            self._unsavedFromOffset = len(self._iList)
        if self._deletesSaved < len(self._deletesList):
            self._save(self._deletesList, self._deletesFilepath, offset=self._deletesSaved, append=True)
            self._deletesSaved = len(self._deletesList)

    def _merge(self):
        if isfile(self._filepath):
            self._rename(self._filepath, self._filepath + '.current')
        if isfile(self._deletesFilepath):
            self._rename(self._deletesFilepath, self._deletesFilepath + '.current')
        self._save(self._iList, self._filepath + '.new', offset=0, append=False)
        self._rename(self._filepath + '.new', self._filepath)
        if isfile(self._filepath + '.current'):
            self._remove(self._filepath + '.current')
        if isfile(self._deletesFilepath + '.current'):
            self._remove(self._deletesFilepath + '.current')
        self._deletesList = IntegerList()
        self._deletesSaved = 0
        self._iList = IntegerList()
        self._iList.extendFrom(self._filepath)
        self._unsavedFromOffset = len(self)

    def _cleanupInCaseOfCrashDuringMerge(self):
        if isfile(self._filepath + '.new'):
            self._remove(self._filepath + '.new')
        if isfile(self._filepath + '.current'):
            if isfile(self._deletesFilepath + '.current'):
                self._rename(self._deletesFilepath + '.current', self._deletesFilepath)
            self._rename(self._filepath + '.current', self._filepath)
        elif isfile(self._deletesFilepath + '.current'):
            self._remove(self._deletesFilepath + '.current')

    def _position(self, element):
        position = bisect_left(self._iList, element)
        if (position < len(self) and element == self[position]):
            return position
        return -1

    def _save(self, list, filepath, offset, append):
        list.save(filepath, offset=offset, append=append)

    def _rename(self, fromPath, toPath):
        rename(fromPath, toPath)

    def _remove(self, filepath):
        remove(filepath)

