## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from __future__ import with_statement
from os import rename, stat
from os.path import isfile
from bisect import bisect_left, bisect_right
from packer import IntPacker

class FileList(object):
    def __init__(self, filename, initialContent=None, packer=IntPacker()):
        self._filename = filename
        self._packer = packer
        isfile(filename) or open(self._filename, 'w')
        self._length = stat(self._filename).st_size/self._packer.length
        if initialContent != None:
            self._writeInitialContent(initialContent)
        self._file = open(self._filename, 'ab+')

    def append(self, item):
        self._append(item)

    def __iter__(self):
        for i in xrange(len(self)):
            yield self[i]

    def close(self):
        if self._file != None:
            self._file.close()

    def __len__(self):
        return self._length

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._slice(index)
        if index < 0:
            index = self._length + index
        if 0 <= index < self._length:
            self._file.seek(index * self._packer.length)
            return self._packer.unpack(self._file.read(self._packer.length))
        raise IndexError('list index out of range')

    def clear(self):
        self._file.seek(0)
        self._file.truncate()
        self._length = 0

    def _slice(self, aSlice):
        return FileListSeq(self, *_sliceWithinRange(aSlice, len(self)))

    def _writeInitialContent(self, initialContent):
        with open(self._filename+'~', 'wb') as self._file:
            self._length = 0
            for item in initialContent:
                self._append(item)
        rename(self._filename+'~',self._filename)

    def _append(self, item):
        self._file.seek(self._length * self._packer.length)
        self._file.write(self._packer.pack(item))
        self._file.flush()
        self._length += 1

class SortedFileList(object):
    def __init__(self, filename, initialContent=None, packer=IntPacker(), mergeTrigger=100):
        self._list = FileList(filename=filename, initialContent=initialContent, packer=packer)
        self._deletedIndexes = FileList(filename=filename+'.deleted', packer=IntPacker())
        self._tempDeletedIndexes = []
        self._mergeTrigger = mergeTrigger
        if len(self._deletedIndexes):
            self._merge()

    def __len__(self):
        return len(self._list) - len(self._tempDeletedIndexes)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return FileListSeq(self, *_sliceWithinRange(index, len(self)))
        if len(self._tempDeletedIndexes):
            if index < 0:
                index += len(self)
            if 0 <= index < len(self):
                extra = 0
                while extra != bisect_right(self._tempDeletedIndexes, index + extra):
                    extra = bisect_right(self._tempDeletedIndexes, index + extra)
                index += extra
        return self._list[index]

    def __iter__(self):
        for i in xrange(len(self)):
            yield self[i]
        
    def __contains__(self, item):
        return self._position(item) > -1

    def index(self, item):
        position = self._position(item)
        if position == -1:
            raise ValueError('list.index(%s): %s not in list' % (item, item))
        return position

    def append(self, item):
        if len(self) > 0 and item <= self[-1]:
            raise ValueError('%s should be greater than %s' % (item, self[-1]))
        self._list.append(item)
    
    def remove(self, item):
        position = self._position(item)
        if position == -1:
            raise ValueError('list.remove(%s): %s not in list' % (item, item))
        realPosition = bisect_left(self._list, item)
        self._tempDeletedIndexes.append(realPosition)
        self._deletedIndexes.append(realPosition)
        self._tempDeletedIndexes.sort()
        if len(self._deletedIndexes) >= self._mergeTrigger:
            self._merge()

    def _position(self, item):
        position = bisect_left(self, item)
        if (position < len(self) and item == self[position]):
            return position
        return -1

    def _merge(self):
        self._tempDeletedIndexes = list(self._deletedIndexes)
        self._tempDeletedIndexes.sort()
        self._list = FileList(self._list._filename, packer=self._list._packer, initialContent=self)
        self._deletedIndexes.clear()
        self._tempDeletedIndexes = []

class FileListSeq(object):
    def __init__(self, mainList, start, stop, step):
        self._mainList = mainList
        self._start = start
        self._stop = stop
        self._step = step

    def __iter__(self):
        for i in range(self._start, self._stop, self._step):
            yield self._mainList[i]

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = _sliceWithinRange(index, len(self))
            nStart = self._start + start * self._step
            nStop = self._start + stop * self._step
            nStep = self._step * step
            return self.__class__(self._mainList, nStart, nStop, nStep)
        if index < 0:
            index = len(self) + index
        index = self._start + index*self._step
        if self._step > 0 and self._start <= index < self._stop:
            return self._mainList[index]
        if self._step < 0 and self._stop < index <= self._start:
            return self._mainList[index]
        raise IndexError('list index out of range')
        

    def __len__(self):
        return abs((self._start - self._stop)/self._step)

def _sliceWithinRange(aSlice, listLength):
        start = aSlice.start or 0
        stop = aSlice.stop or listLength
        step = aSlice.step or 1
        if stop < 0:
            stop += listLength
        if stop > listLength:
            stop = listLength
        if start < 0:
            start += listLength
        if start < 0:
            start = 0
        if step < 0:
            start,stop = stop-1, start-1
        return start, stop, step
