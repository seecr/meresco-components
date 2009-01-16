from __future__ import with_statement
from os import rename
from os.path import isfile

class SortedFileList(object):
    def __init__(self, filename, initialContent=[], contentType=int):
        self._filename = filename
        self._file = None
        isfile(filename) or file(self._filename, 'w')
        self._contentType = contentType
        if initialContent:
            with open(self._filename+'~', 'w') as self._file:
                for item in initialContent:
                    self._appendToFile(item)
            self._file = None
            rename(self._filename+'~',self._filename)

    def append(self, item):
        self._appendToFile(item)

    def __iter__(self):
        with open(self._filename) as f:
            for line in f:
                yield self._contentType(line[:-len('\n')])

    def close(self):
        if self._file != None:
            self._file.close()
            self._file = None

    def _appendToFile(self, item):
        if self._file == None:
            self._file = file(self._filename, 'a')
        self._file.write('%s\n'% item)
        self._file.flush()
