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
from os.path import isdir, join
from os import makedirs, listdir, rename
from storage.storage import escapeName, unescapeName
from time import time, strftime, localtime, mktime, strptime
from meresco.components.sorteditertools import OrIterator, AndIterator, WrapIterable
from meresco.components import SortedFileList, DoubleUniqueBerkeleyDict, BerkeleyDict
from sys import maxint

from bisect import bisect_left

MERGE_TRIGGER = 1000
SETSPEC_SEPARATOR = ','

class OaiJazz(object):
    def __init__(self, aDirectory):
        self._directory = aDirectory
        if isdir(join(aDirectory, 'sets')):
            assert isdir(join(aDirectory, 'identifier2setSpecs')), "This is an old OaiJazz data storage which doesn't have the identifier2setSpecs directory. Please convert manually or rebuild complete data storage."
        isdir(join(aDirectory, 'stamp2identifier')) or makedirs(join(aDirectory,'stamp2identifier'))
        isdir(join(aDirectory, 'identifier2setSpecs')) or makedirs(join(aDirectory,'identifier2setSpecs'))
        isdir(join(aDirectory, 'sets')) or makedirs(join(aDirectory,'sets'))
        isdir(join(aDirectory, 'prefixes')) or makedirs(join(aDirectory,'prefixes'))
        isdir(join(aDirectory, 'prefixesInfo')) or makedirs(join(aDirectory,'prefixesInfo'))
        self._prefixes = {}
        self._sets = {}
        self._stamp2identifier = DoubleUniqueBerkeleyDict(join(self._directory, 'stamp2identifier'))
        self._tombStones = SortedFileList(join(self._directory, 'tombStones.list'),
        mergeTrigger=MERGE_TRIGGER)
        self._identifier2setSpecs = BerkeleyDict(join(self._directory, 'identifier2setSpecs'))
        self._read()

    def addOaiRecord(self, identifier, sets=None, metadataFormats=None):
        sets = [] if sets == None else sets
        metadataFormats = [] if metadataFormats == None else metadataFormats
        assert [prefix for prefix, schema, namespace in metadataFormats], 'No metadataFormat specified for record with identifier "%s"' % identifier
        for setSpec, setName in sets:
            assert SETSPEC_SEPARATOR not in setSpec, 'SetSpec "%s" contains illegal characters' % setSpec
        oldPrefixes, oldSets = self._delete(identifier)
        stamp = self._stamp()
        prefixes = set(prefix for prefix, schema, namespace in metadataFormats)
        prefixes.update(oldPrefixes)
        setSpecs = _flattenSetHierarchy((setSpec for setSpec, setName in sets))
        setSpecs.update(oldSets)
        self._add(stamp, identifier, setSpecs, prefixes)
        self._storeMetadataFormats(metadataFormats)

    def delete(self, identifier):
        oldPrefixes, oldSets = self._delete(identifier)
        if not oldPrefixes:
            return
        stamp = self._stamp()
        self._add(stamp, identifier, oldSets, oldPrefixes)
        self._tombStones.append(stamp)

    def oaiSelect(self, sets=None, prefix='oai_dc', continueAfter='0', oaiFrom=None, oaiUntil=None, batchSize='ignored'):
        sets = [] if sets == None else sets
        start = max(int(continueAfter)+1, self._fromTime(oaiFrom))
        stop = self._untilTime(oaiUntil)
        stampIds = self._prefixes.get(prefix, [])
        if stop:
            stampIds = stampIds[bisect_left(stampIds,start):bisect_left(stampIds,stop)]
        else:
            stampIds = stampIds[bisect_left(stampIds,start):]
        if sets:
            allStampIdsFromSets = (self._sets.get(setSpec,[]) for setSpec in sets)
            stampIds = AndIterator(stampIds,
                reduce(OrIterator, allStampIdsFromSets))
        #WrapIterable to fool Observable's any message
        return WrapIterable((RecordId(self._getIdentifier(stampId), stampId) for stampId in stampIds))

    def getDatestamp(self, identifier):
        stamp = self.getUnique(identifier)
        if stamp == None:
            return None
        return strftime('%Y-%m-%dT%H:%M:%SZ', localtime(stamp/1000000.0))

    def getUnique(self, identifier):
        if hasattr(identifier, 'stamp'):
            return identifier.stamp
        return self._getStamp(identifier)

    def isDeleted(self, identifier):
        stamp = self.getUnique(identifier)
        if stamp == None:
            return False
        return stamp in self._tombStones

    def getAllMetadataFormats(self):
        return WrapIterable(self._getAllMetadataFormats())

    def getAllPrefixes(self):
        return self._prefixes.keys()

    def getSets(self, identifier):
        if identifier not in self._identifier2setSpecs:
            return []
        return self._identifier2setSpecs[identifier].split(SETSPEC_SEPARATOR)

    def getPrefixes(self, identifier):
        stamp = self.getUnique(identifier)
        if not stamp:
            return []
        return WrapIterable((prefix for prefix, stampIds in self._prefixes.items() if stamp in stampIds))

    def getAllSets(self):
        return self._sets.keys()
        
    def getNrOfRecords(self, prefix='oai_dc'):
        return len(self._prefixes.get(prefix, []))

    # private methods

    def _add(self, stamp, identifier, setSpecs, prefixes):
        try:
            for setSpec in setSpecs:
                self._getSetList(setSpec).append(stamp)
            for prefix in prefixes:
                self._getPrefixList(prefix).append(stamp)
            self._stamp2identifier[str(stamp)]=identifier
            if setSpecs:
                self._identifier2setSpecs[identifier] = SETSPEC_SEPARATOR.join(setSpecs) 
        except ValueError, e:
            self._rollback(stamp, identifier, setSpecs, prefixes)
            raise ValueError('Timestamp error, original message: "%s"' % str(e))

    def _rollback(self, stamp, identifier, setSpecs, prefixes):
        for setSpec in setSpecs:
            try:
                self._getSetList(setSpec).remove(stamp)
            except ValueError:
                pass #ignored because stamp could not have been added.
        for prefix in prefixes:
            try:
                self._getPrefixList(prefix).remove(stamp)
            except ValueError:
                pass #ignored because stamp could not have been added.


    def _getAllMetadataFormats(self):
        for prefix in self._prefixes.keys():
            schema = open(join(self._directory, 'prefixesInfo', '%s.schema' % escapeName(prefix))).read()
            namespace = open(join(self._directory, 'prefixesInfo', '%s.namespace' % escapeName(prefix))).read()
            yield (prefix, schema, namespace)

    def _getSetList(self, setSpec):
        if setSpec not in self._sets:
            filename = join(self._directory, 'sets', '%s.list' % escapeName(setSpec))
            self._sets[setSpec] = SortedFileList(filename, mergeTrigger=MERGE_TRIGGER)
        return self._sets[setSpec]

    def _getPrefixList(self, prefix):
        if prefix not in self._prefixes:
            filename = join(self._directory, 'prefixes', '%s.list' % escapeName(prefix))
            self._prefixes[prefix] = SortedFileList(filename, mergeTrigger=MERGE_TRIGGER)
        return self._prefixes[prefix]

    def _fromTime(self, oaiFrom):
        if not oaiFrom:
            return 0
        return self._timeToNumber(oaiFrom)

    def _untilTime(self, oaiUntil):
        if not oaiUntil:
            return None
        UNTIL_IS_INCLUSIVE = 1 # Add one second to 23:59:59
        return self._timeToNumber(oaiUntil) + UNTIL_IS_INCLUSIVE

    @staticmethod
    def _timeToNumber(time):
        try:
            return int(mktime(strptime(time, '%Y-%m-%dT%H:%M:%SZ'))*1000000.0)
        except (ValueError, OverflowError):
            return maxint * 1000000


    def _getIdentifier(self, stamp):
        return self._stamp2identifier.get(str(stamp), None)

    def _getStamp(self, identifier):
        result = self._stamp2identifier.getKeyFor(identifier)
        if result != None:
            result = int(result)
        return result

    def _delete(self, identifier):
        stamp = self.getUnique(identifier)
        stamp in self._tombStones and self._tombStones.remove(stamp)
        oldPrefixes = []
        oldSets = []
        if stamp != None:
            del self._stamp2identifier[str(stamp)]
            for prefix, prefixStamps in self._prefixes.items():
                if stamp in prefixStamps:
                    oldPrefixes.append(prefix)
                    prefixStamps.remove(stamp)
            if identifier in self._identifier2setSpecs:
                oldSets = self._identifier2setSpecs[identifier].split(SETSPEC_SEPARATOR)
                for setSpec in oldSets:
                    self._sets[setSpec].remove(stamp)
                del self._identifier2setSpecs[identifier]
        return oldPrefixes, oldSets

    def _read(self):
        for prefix in (unescapeName(name[:-len('.list')]) for name in listdir(join(self._directory, 'prefixes')) if name.endswith('.list')):
            self._getPrefixList(prefix)
        for setSpec in (unescapeName(name[:-len('.list')]) for name in listdir(join(self._directory, 'sets')) if name.endswith('.list')):
            self._getSetList(setSpec)

    def _storeMetadataFormats(self, metadataFormats):
        for prefix, schema, namespace in metadataFormats:
            _write(join(self._directory, 'prefixesInfo', '%s.schema' % escapeName(prefix)), schema)
            _write(join(self._directory, 'prefixesInfo', '%s.namespace' % escapeName(prefix)), namespace)

    def _stamp(self):
        """time in microseconds"""
        return int(time()*1000000.0)

# helper methods

class RecordId(str):
    def __new__(self, identifier, stamp):
        return str.__new__(self, identifier)
    def __init__(self, identifier, stamp):
        self.stamp = stamp
    def __getslice__(self, *args, **kwargs):
        return RecordId(str.__getslice__(self, *args, **kwargs), self.stamp)

def _writeLines(filename, lines):
    with open(filename + '.tmp', 'w') as f:
        for line in lines:
            f.write('%s\n' % line)
    rename(filename + '.tmp', filename)

def _write(filename, content):
    with open(filename + '.tmp', 'w') as f:
        f.write(content)
    rename(filename + '.tmp', filename)

def _flattenSetHierarchy(sets):
    """"[1:2:3, 1:2:4] => [1, 1:2, 1:2:3, 1:2:4]"""
    result = set()
    for setSpec in sets:
        parts = setSpec.split(':')
        for i in range(1, len(parts) + 1):
            result.add(':'.join(parts[:i]))
    return result

