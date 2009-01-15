## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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
from itertools import takewhile, dropwhile
from os.path import join, isfile

class SegmentInfo(object):
    def __init__(self, length, offset):
        self.length = length
        self.offset = offset
    def __repr__(self):
        return '%d@%d' % (self.length, self.offset)
    def __eq__(self, other):
        return \
            type(other) == SegmentInfo and \
            other.length == self.length and \
            other.offset == self.offset

class LuceneDocIdTracker(object):
    """
        This class tracks docids for Lucene version 2.2.0
                                                    =====
    """
    def __init__(self, mergeFactor, maxDoc=0, directory=None):
        assert directory != None
        self._directory = directory
        self._mergeFactor = mergeFactor
        self._ramSegmentsInfo = []
        self._segmentInfo = []
        self._nextDocId = maxDoc
        self._docIds = range(maxDoc)
        if isfile(join(directory, 'tracker.segments')):
            self._load()
        else:
            if maxDoc > 0:
                self._segmentInfo.append(SegmentInfo(maxDoc, 0))

    def next(self):
        self._ramSegmentsInfo.append(SegmentInfo(1, len(self._docIds)))
        self._docIds.append(self._nextDocId)
        self._nextDocId += 1
        if len(self._ramSegmentsInfo) >= self._mergeFactor:
            self._flushRamSegments()
        return self._nextDocId - 1

    def _flushRamSegments(self):
        if len(self._ramSegmentsInfo) > 0:
            self._merge(self._ramSegmentsInfo, self._ramSegmentsInfo[0].offset, 0, self._mergeFactor)
            self._segmentInfo.append(self._ramSegmentsInfo[0])
            self._ramSegmentsInfo = []
            self._maybeMerge(self._segmentInfo, lower = 0, upper = self._mergeFactor)
        self._save()

    def _maybeMerge(self, segments, lower, upper):
        reversedSegments = reversed(segments)
        worthySegments = list(takewhile(lambda si: si.length <= upper,
            dropwhile(lambda si: not lower < si.length <= upper , reversedSegments)))
        nrOfWorthySegments = len(worthySegments)
        if nrOfWorthySegments == self._mergeFactor:
            self._merge(segments, worthySegments[-1].offset, lower, upper)

    def _merge(self, segments, newOffset, lower, upper):
        merged = [docid for docid in self._docIds[newOffset:] if docid >= 0]
        del self._docIds[newOffset:] # ook op disk
        self._docIds.extend(merged)
        newLength = len(merged)
        si = SegmentInfo(newLength, newOffset)
        del segments[-self._mergeFactor:]
        segments.append(si)
        if newLength > upper:
            self._maybeMerge(segments, lower=upper, upper=upper*self._mergeFactor)

    def deleteDocId(self, docid):
        assert self._docIds[docid] != -1
        removedUDocID = self._docIds[docid]
        self._docIds[docid] = -1
        self._flushRamSegments()
        return removedUDocID

    def map(self, luceneIds):
        return (self._docIds[luceneId] for luceneId in luceneIds)

    def flush(self):
        self._flushRamSegments()

    def _save(self):
        filename = join(self._directory, 'tracker.segments')
        f = open(filename, 'w')
        f.write(str(self._mergeFactor))
        f.write('\n')
        f.write(str(self._nextDocId))
        f.write('\n')
        f.write(str(self._segmentInfo))
        f.close()

        lastSegmentIndex = len(self._segmentInfo) - 1
        filename = join(self._directory, str(lastSegmentIndex) + '.docids')
        f = open(filename, 'w')
        f.write(repr(self._docIds[self._segmentInfo[lastSegmentIndex].offset:]))
        f.close()

    def _load(self):
        f = open(join(self._directory, 'tracker.segments'))
        self._mergeFactor = int(f.next().strip())
        self._nextDocId = int(f.next().strip())
        segments = [segment.split("@") for segment in f.next().strip()[1:-1].split(",")]
        for segmentData in segments:
            length, offset = map(int, segmentData)
            self._segmentInfo.append(SegmentInfo(length, offset))
        for i in range(len(self._segmentInfo)):
            f = open(join(self._directory, str(i) + '.docids'))
            self._docIds.extend(eval(f.read()))
            f.close()

    def __eq__(self, other):
        return type(other) == type(self) and \
            self._mergeFactor == other._mergeFactor and \
            self._nextDocId == other._nextDocId and \
            self._docIds == other._docIds and \
            self._segmentInfo == other._segmentInfo and \
            self._ramSegmentsInfo == other._ramSegmentsInfo

    def __repr__(self):
        return 'tracker:' + repr(self._mergeFactor) + '/' + repr(self._nextDocId) + repr(self._segmentInfo) + repr(self._ramSegmentsInfo)

    def close(self):
        self.flush()
