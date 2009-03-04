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

from integerlist import IntegerList

class SegmentInfo(object):
    def __init__(self, length, offset, filename, cleanup=True):
        self.length = length
        self.offset = offset
        self._deleted = []
        self._filename = filename
        if cleanup:
            open(filename, 'w').close()

    def __repr__(self):
        return '%d@%d' % (self.length, self.offset)

    def __eq__(self, other):
        return \
            type(other) == SegmentInfo and \
            other.length == self.length and \
            other.offset == self.offset and \
            other._deleted == self._deleted

    def deleteLuceneId(self, luceneId):
        self._deleted.append(luceneId)

    def deletedLuceneIds(self):
        return (int(s) for s in open(self._filename))

    def saveDeleted(self):
        f = open(self._filename, 'a')
        for i in self._deleted:
            f.write(str(i) + '\n')
        f.close()
        self._deleted = []

class LuceneDocIdTrackerException(Exception):
    pass

class LuceneDocIdTracker(object):
    """
        This class tracks docids for Lucene version 2.2.0
                                                    =====
    """
    def __init__(self, mergeFactor, directory=None, maxDoc=0):
        assert directory != None
        self._directory = directory
        self._mergeFactor = mergeFactor
        self._ramSegmentsInfo = []
        self._segmentInfo = []
        self._nextDocId = 0
        self._docIds = IntegerList()
        if isfile(join(directory, 'tracker.segments')):
            self._load()
        else:
            if maxDoc > 0:
                self._initializeFromOptimizedIndex(maxDoc)

    def _newSegmentInfo(self, length, offset, cleanup=True):
        segmentNr = len(self._segmentInfo)
        filename = join(self._directory, str(segmentNr) + '.deleted')
        return SegmentInfo(length, offset, filename, cleanup)

    def _initializeFromOptimizedIndex(self, maxDoc):
        self._nextDocId = maxDoc
        self._docIds = IntegerList(maxDoc)
        self._segmentInfo.append(self._newSegmentInfo(maxDoc, 0))
        self._save()

    def next(self):
        self._ramSegmentsInfo.append(self._newSegmentInfo(1, len(self._docIds)))
        self._docIds.append(self._nextDocId)
        self._nextDocId += 1
        if len(self._ramSegmentsInfo) >= self._mergeFactor:
            self._flushRamSegments()
        return self._nextDocId - 1

    def getMap(self):
        return self._docIds.copy()

    def mapLuceneId(self, luceneId):
        return self._docIds[luceneId]

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
        newSegmentLength = self._docIds.mergeFromOffset(newOffset)
        si = self._newSegmentInfo(newSegmentLength, newOffset)
        del segments[-self._mergeFactor:]
        segments.append(si)
        if newSegmentLength > upper:
            self._maybeMerge(segments, lower=upper, upper=upper*self._mergeFactor)

    def deleteLuceneId(self, luceneId):
        assert self._docIds[luceneId] != -1, (self._docIds, luceneId)
        docId = self._docIds[luceneId]
        self._docIds[luceneId] = -1
        self._segmentForLuceneId(luceneId).deleteLuceneId(luceneId)
        self._flushRamSegments()
        return docId

    def isDeleted(self, luceneId):
        return self._docIds[luceneId] == -1

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
        for segment in self._segmentInfo:
            segment.saveDeleted()
        lastSegmentIndex = len(self._segmentInfo) - 1
        filename = join(self._directory, str(lastSegmentIndex) + '.docids')
        self._docIds.save(filename, self._segmentInfo[lastSegmentIndex].offset)

    def _load(self):
        if len(self._docIds) != 0:
            raise LuceneDocIdTrackerException('DocIdList not empty on load')
        f = open(join(self._directory, 'tracker.segments'))
        self._mergeFactor = int(f.next().strip())
        self._nextDocId = int(f.next().strip())
        segments = [segment.split("@") for segment in f.next().strip()[1:-1].split(",")]
        for i, segmentData in enumerate(segments):
            length, offset = int(segmentData[0]), int(segmentData[1])
            segment = self._newSegmentInfo(length, offset, cleanup=False)
            self._segmentInfo.append(segment)

        for i, segment in enumerate(self._segmentInfo):
            self._docIds.extendFrom(join(self._directory, str(i) + '.docids'))
            for deleted in segment.deletedLuceneIds():
                self._docIds[deleted] = -1

    def __eq__(self, other):
        return type(other) == type(self) and \
            self._mergeFactor == other._mergeFactor and \
            self._nextDocId == other._nextDocId and \
            self._docIds == other._docIds and \
            self._segmentInfo == other._segmentInfo and \
            self._ramSegmentsInfo == other._ramSegmentsInfo

    def __repr__(self):
        return 'tracker:' + repr(self._mergeFactor) + '/' + repr(self._nextDocId) + repr(self._segmentInfo) + repr(self._ramSegmentsInfo) + repr(self._docIds)

    def _segmentForLuceneId(self, luceneId):
        def find(segments, luceneId):
            for segment in segments:
                if segment.offset + segment.length >= luceneId:
                    return segment
            return None

        result = find(self._segmentInfo, luceneId)
        if result != None:
            return result
        result = find(self._ramSegmentsInfo, luceneId)
        if result == None:
            raise Exception("Can't find luceneId %s in %s" % (luceneId, self))
        return result

    def close(self):
        self.flush()
