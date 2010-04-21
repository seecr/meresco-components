# -*- coding: utf-8 -*-
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
    def __init__(self, length, offset):
        self.length = length
        self.offset = offset
        self._deleted = IntegerList()
        self._filename = None

    def openIfNew(self, filename):
        if not self._filename:
            self.open(filename)

    def open(self, filename, cleanup=True):
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
        l = IntegerList()
        l.extendFrom(self._filename)
        return l

    def saveDeleted(self):
        self._deleted.extendTo(self._filename)
        self._deleted = IntegerList()

class LuceneDocIdTrackerException(Exception):
    pass

def trackerBisect(a, x, lo=0, hi=None):
    """This bisect is based on bisect_left from the bisect module.
    This implementation will take into account that elements in a
    can be -1 and all other elements are sorted and >= 0"""
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = midKeep = (lo+hi)//2
        while a[mid] == -1 and mid > lo:
            mid -= 1
        if a[mid] == -1: lo = midKeep+1
        elif a[mid] < x: lo = mid+1
        else: hi = mid
    return lo

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

    def _initializeFromOptimizedIndex(self, maxDoc):
        self._nextDocId = maxDoc
        self._docIds = IntegerList(maxDoc)
        self._segmentInfo.append(SegmentInfo(maxDoc, 0))
        self._save()

    def _maybeFlushRamSegments(self):
        if len(self._ramSegmentsInfo) >= self._mergeFactor:
            self._flushRamSegments()

    def next(self):
        self._ramSegmentsInfo.append(SegmentInfo(1, len(self._docIds)))
        self._docIds.append(self._nextDocId)
        self._nextDocId += 1
        self._maybeFlushRamSegments()
        return self._nextDocId - 1

    def getMap(self):
        return self._docIds.copy()

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
        if nrOfWorthySegments >= self._mergeFactor:
            self._merge(segments, worthySegments[-1].offset, lower, upper)

    def _merge(self, segments, newOffset, lower, upper):
        newSegmentLength = self._docIds.mergeFromOffset(newOffset)
        si = SegmentInfo(newSegmentLength, newOffset)
        del segments[-self._mergeFactor:]
        segments.append(si)
        if newSegmentLength > upper:
            self._maybeMerge(segments, lower=upper, upper=upper*self._mergeFactor)

    def deleteDocId(self, docId):
        position = trackerBisect(self._docIds, docId)
        if position < len(self._docIds) and self._docIds[position] == docId:
            self._docIds[position] = -1
            self._segmentForLuceneId(position).deleteLuceneId(position)
            #self._maybeFlushRamSegments()
            return True
        return False

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
        if self._segmentInfo:
            segmentNr = len(self._segmentInfo) - 1
            self._segmentInfo[-1].openIfNew(join(self._directory, str(segmentNr) + '.deleted'))
        for segment in self._segmentInfo:
            segment.saveDeleted()
        lastSegmentIndex = len(self._segmentInfo) - 1
        filename = join(self._directory, str(lastSegmentIndex) + '.docids')
        if lastSegmentIndex >= 0:
            lastSegmentInfo = self._segmentInfo[lastSegmentIndex]
            if lastSegmentInfo.length > 0:
                self._docIds.save(filename, lastSegmentInfo.offset)

    def _load(self):
        if len(self._docIds) != 0:
            raise LuceneDocIdTrackerException('DocIdList not empty on load')
        f = open(join(self._directory, 'tracker.segments'))
        self._mergeFactor = int(f.next().strip())
        self._nextDocId = int(f.next().strip())
        segments = [segment.split("@") for segment in f.next().strip()[1:-1].split(",")]
        for i, segmentData in enumerate(segments):
            length, offset = int(segmentData[0]), int(segmentData[1])
            segment = SegmentInfo(length, offset)
            filename = join(self._directory, str(i) + '.deleted')
            segment.open(filename, cleanup=False)
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
        for segment in reversed(self._ramSegmentsInfo):
            if luceneId >= segment.offset and luceneId < segment.offset + segment.length:
                return segment
        for segment in reversed(self._segmentInfo):
            if luceneId >= segment.offset and luceneId < segment.offset + segment.length:
                return segment
        raise Exception("Can't find luceneId %s in %s" % (luceneId, self))


    def close(self):
        self.flush()

    def nrOfDocs(self):
        return len([docId for docId in self._docIds if docId != -1])
