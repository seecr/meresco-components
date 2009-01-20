from __future__ import with_statement
from os import rename, stat
from os.path import isfile
from struct import pack, unpack
from bisect import bisect_left

FORMAT = 'Q'
FORMAT_LENGTH=8

class SortedFileList(object):
    def __init__(self, filename, initialContent=[]):
        self._filename = filename
        isfile(filename) or open(self._filename, 'w')
        self._length = stat(self._filename).st_size/FORMAT_LENGTH
        if initialContent:
            self._writeInitialContent(initialContent)
        self._file = open(self._filename, 'ab+')

    def _writeInitialContent(self, initialContent):
        with open(self._filename+'~', 'wb') as self._file:
            self._length = 0
            for item in initialContent:
                self._appendToopen(item)
        rename(self._filename+'~',self._filename)

    def append(self, anInteger):
        self._appendToopen(anInteger)

    def __iter__(self):
        for i in xrange(self._length):
            yield self[i]

    def close(self):
        if self._file != None:
            self._file.close()

    def _appendToopen(self, item):
        self._file.seek(self._length * FORMAT_LENGTH)
        self._file.write(pack(FORMAT, item))
        self._file.flush()
        self._length += 1

    def __len__(self):
        return self._length

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._slice(index)
        if index < 0:
            index = self._length + index
        if 0 <= index < self._length:
            self._file.seek(index * FORMAT_LENGTH)
            (result,) = unpack(FORMAT, self._file.read(FORMAT_LENGTH))
            return result
        raise IndexError('list index out of range')

    def _slice(self, aSlice):
        return self.SortedFileListSeq(self, *_sliceWithinRange(aSlice, self._length))

    def __contains__(self, item):
        position = bisect_left(self, item)
        return position < self._length and item == self[position]

    class SortedFileListSeq(object):
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
                start,stop, step = _sliceWithinRange(index, len(self))
                nStart = self._start + start * self._step
                nStop = self._start + stop * self._step
                nStep = self._step * step
                return self.__class__(self._mainList, nStart, nStop, nStep)
            return self._mainList[self._start + index*self._step]

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