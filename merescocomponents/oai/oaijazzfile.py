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

from __future__ import with_statement
from os.path import isdir, join, isfile
from os import makedirs, listdir, rename
from storage.storage import escapeName, unescapeName
from time import time, strftime, localtime, mktime, strptime
from itertools import ifilter, dropwhile, takewhile, chain
from merescocomponents.sorteditertools import OrIterator, AndIterator, WrapIterable
from merescocomponents import SortedFileList
from merescocore.framework import getCallstackVar
from bisect import bisect_left

class OaiJazzFile(object):
    def __init__(self, aDirectory, transactionName='oai'):
        self._directory = aDirectory
        isdir(aDirectory) or makedirs(aDirectory)
        isdir(join(aDirectory, 'sets')) or makedirs(join(aDirectory,'sets'))
        isdir(join(aDirectory, 'prefixes')) or makedirs(join(aDirectory,'prefixes'))
        isdir(join(aDirectory, 'prefixesInfo')) or makedirs(join(aDirectory,'prefixesInfo'))
        self._prefixes = {}
        self._sets = {}
        self._stamp2identifier = {}
        self._identifier2stamp = {}
        self._tombStones = self._createList('', 'tombStones')
        self._deletedStamps = set()
        self._read()
        self._transactionName = transactionName

    def addOaiRecord(self, identifier, sets=[], metadataFormats=[]):
        assert [prefix for prefix, schema, namespace in metadataFormats], 'No metadataFormat specified for record with identifier "%s"' % identifier
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

    def oaiSelect(self, sets=[], prefix='oai_dc', continueAfter='0', oaiFrom=None, oaiUntil=None, batchSize='ignored'):
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
        return WrapIterable((RecordId(self._stamp2identifier.get(stampId), stampId) for stampId in ifilter(lambda stampId: stampId not in self._deletedStamps, stampIds)))

    def getDatestamp(self, identifier):
        stamp = self.getUnique(identifier)
        if stamp == None:
            return None
        return strftime('%Y-%m-%dT%H:%M:%SZ', localtime(stamp/1000000.0))

    def getUnique(self, identifier):
        if hasattr(identifier, 'stamp'):
            return identifier.stamp
        return self._identifier2stamp.get(identifier, None)

    def isDeleted(self, identifier):
        stamp = self.getUnique(identifier)
        if stamp == None:
            return False
        return stamp in self._tombStones

    def getAllMetadataFormats(self):
        for prefix in self._prefixes.keys():
            schema = open(join(self._directory, 'prefixesInfo', '%s.schema' % escapeName(prefix))).read()
            namespace = open(join(self._directory, 'prefixesInfo', '%s.namespace' % escapeName(prefix))).read()
            yield (prefix, schema, namespace)

    def getAllPrefixes(self):
        return self._prefixes.keys()

    def getSets(self, identifier):
        stamp = self.getUnique(identifier)
        if not stamp:
            return []
        return WrapIterable((setSpec for setSpec, stampIds in self._sets.items() if stamp in stampIds))

    def getPrefixes(self, identifier):
        stamp = self.getUnique(identifier)
        if not stamp:
            return []
        return WrapIterable((prefix for prefix, stampIds in self._prefixes.items() if stamp in stampIds))

    def getAllSets(self):
        return self._sets.keys()

    def begin(self):
        tx = getCallstackVar('tx')
        if tx.name == self._transactionName:
            tx.join(self)

    def commit(self):
        if self._deletedStamps:
            for prefix, prefixStamps in self._prefixes.items():
                self._prefixes[prefix] = self._createList('prefixes', prefix, (stamp for stamp in prefixStamps if not stamp in self._deletedStamps))
            for setSpec, setStamps in self._sets.items():
                self._sets[setSpec] = self._createList('sets', setSpec, (stamp for stamp in setStamps if not stamp in self._deletedStamps))
            self._tombStones = self._createList('', 'tombStones',  (stamp for stamp in self._tombStones if not stamp in self._deletedStamps))
        _writeLines(join(self._directory, 'identifiers'), ('%s %s' % (stamp,identifier) for identifier,stamp in self._identifier2stamp.items() if not stamp in self._deletedStamps))
        self._deletedStamps = set()

    def rollback(self):
        pass

    # private methods
    
    def _add(self, stamp, identifier, setSpecs, prefixes):
        for setSpec in setSpecs:
            self._sets.setdefault(setSpec, self._createList('sets', setSpec)).append(stamp)
        for prefix in prefixes:
            self._prefixes.setdefault(prefix, self._createList('prefixes', prefix)).append(stamp)
        self._stamp2identifier[stamp]=identifier
        self._identifier2stamp[identifier]=stamp

    def _createList(self, subdir, name, initialContent=None):
        filename = join(self._directory, subdir, escapeName(name))
        return SortedFileList(filename, initialContent=initialContent)

    def _fromTime(self, oaiFrom):
        if not oaiFrom:
            return 0
        return int(mktime(strptime(oaiFrom, '%Y-%m-%dT%H:%M:%SZ'))*1000000.0)
    
    def _untilTime(self, oaiUntil):
        if not oaiUntil:
            return None
        UNTIL_IS_INCLUSIVE = 1 # Add one second to 23:59:59
        return int(mktime(strptime(oaiUntil, '%Y-%m-%dT%H:%M:%SZ'))*1000000.0) + UNTIL_IS_INCLUSIVE
        
    def _delete(self, identifier):
        stamp = self.getUnique(identifier)
        oldPrefixes = []
        oldSets = []
        if stamp != None:
            for prefix, prefixStamps in self._prefixes.items():
                if stamp in prefixStamps:
                    oldPrefixes.append(prefix)
            for setSpec, setStamps in self._sets.items():
                if stamp in setStamps:
                    oldSets.append(setSpec)
            self._deletedStamps.add(stamp)
        return oldPrefixes, oldSets

    def _read(self):
        for prefix in (unescapeName(name) for name in listdir(join(self._directory, 'prefixes'))):
            self._prefixes[prefix] = self._createList('prefixes', prefix)
        for setSpec in (unescapeName(name) for name in listdir(join(self._directory, 'sets'))):
            self._sets[setSpec] = self._createList('sets', setSpec)
        self._stamp2identifier = {}
        self._identifier2stamp = {}
        identifiersFile = join(self._directory, 'identifiers')
        if isfile(identifiersFile):
            with open(identifiersFile) as f:
                for stamp, identifier in (line.strip().split(' ',1) for line in f):
                    self._stamp2identifier[int(stamp)] = identifier
                    self._identifier2stamp[identifier] = int(stamp)

    def _storeMetadataFormats(self, metadataFormats):
        for prefix, schema, namespace in metadataFormats:
            _write(join(self._directory, 'prefixesInfo', '%s.schema' % escapeName(prefix)), schema)
            _write(join(self._directory, 'prefixesInfo', '%s.namespace' % escapeName(prefix)), namespace)

    def _store(self):
        pass

    def _stamp(self):
        """time in microseconds"""
        return int(time()*1000000.0)

# helper methods

class RecordId(str):
    def __new__(self, identifier, stamp):
        return str.__new__(self, identifier)
    def __init__(self, identifier, stamp):
        self.stamp = stamp

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
    
