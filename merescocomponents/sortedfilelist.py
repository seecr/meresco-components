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
        start = aSlice.start or 0
        stop = aSlice.stop or self._length
        step = aSlice.step or 1
        if stop < 0:
            stop += self._length
        if stop > self._length:
            stop = self._length
        if start < 0:
            start += self._length
        if start < 0:
            start = 0
        if step < 0:
            start,stop = stop-1, start-1
        for i in range(start, stop, step):
            yield self[i]

    def __contains__(self, item):
        position = bisect_left(self, item)
        return position < self._length and item == self[position]
