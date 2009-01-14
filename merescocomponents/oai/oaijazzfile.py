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
from merescocore.framework import Observable
from os.path import isdir, join, isfile
from os import makedirs, listdir, rename
from storage.storage import escapeName, unescapeName
from time import time, strftime, localtime, mktime, strptime
from itertools import ifilter, dropwhile, takewhile
from merescocomponents.sorteditertools import OrIterator, AndIterator

class OaiJazzFile(Observable):
    def __init__(self, aDirectory):
        self._directory = aDirectory
        isdir(aDirectory) or makedirs(aDirectory)
        isdir(join(aDirectory, 'sets')) or makedirs(join(aDirectory,'sets'))
        isdir(join(aDirectory, 'prefixes')) or makedirs(join(aDirectory,'prefixes'))
        self._prefixes = {}
        self._sets = {}
        self._stamp2identifier = {}
        self._identifier2stamp = {}
        self._deleted = set()
        self._read()

    def addOaiRecord(self, identifier, sets=[], metadataFormats=[]):
        assert [prefix for prefix, schema, namespace in metadataFormats], 'No metadataFormat specified for record with identifier "%s"' % identifier
        self._delete(identifier)
        stamp = self._stamp()
        prefixes = (prefix for prefix, schema, namespace in metadataFormats)
        setSpecs = _flattenSetHierarchy((setSpec for setSpec, setName in sets))
        self._add(stamp, identifier, setSpecs, prefixes)
        self._store(metadataFormats)

    def delete(self, identifier):
        oldPrefixes, oldSets = self._delete(identifier)
        if not oldPrefixes:
            return
        stamp = self._stamp()
        self._add(stamp, identifier, oldSets, oldPrefixes)
        self._deleted.add(stamp)
        self._store()

    def oaiSelect(self, sets=[], prefix='oai_dc', continueAt='0', oaiFrom=None, oaiUntil=None):
        stampIds = dropwhile(lambda stamp: stamp <= int(continueAt),
            dropwhile(self._fromPredicate(oaiFrom),
                takewhile(self._untilPredicate(oaiUntil),
                    (self._prefixes.get(prefix, [])))))
        if sets:
            allStampIdsFromSets = (self._sets.get(setSpec,[]) for setSpec in sets)
            stampIds = AndIterator(stampIds,
                reduce(OrIterator, allStampIdsFromSets))
        return (self._stamp2identifier.get(stampId) for stampId in stampIds)

    def getDatestamp(self, identifier):
        stamp = self._identifier2stamp.get(identifier, None)
        if stamp == None:
            return None
        return strftime('%Y-%m-%dT%H:%M:%SZ', localtime(stamp/1000000.0))

    def getUnique(self, identifier):
        return self._identifier2stamp.get(identifier, None)

    def isDeleted(self, identifier):
        stamp = self._identifier2stamp.get(identifier, None)
        return stamp != None and stamp in self._deleted

    def getAllMetadataFormats(self):
        for prefix in self._prefixes.keys():
            schema = open(join(self._directory, 'prefixes', '%s.schema' % escapeName(prefix))).read()
            namespace = open(join(self._directory, 'prefixes', '%s.namespace' % escapeName(prefix))).read()
            yield (prefix, schema, namespace)

    def getAllPrefixes(self):
        return self._prefixes.keys()

    def getSets(self, identifier):
        stamp = self._identifier2stamp.get(identifier, None)
        if not stamp:
            return
        for setSpec, stampIds in self._sets.items():
            if stamp in stampIds:
                yield setSpec

    def getPrefixes(self, identifier):
        stamp = self._identifier2stamp.get(identifier, None)
        if not stamp:
            return
        for prefix, stampIds in self._prefixes.items():
            if stamp in stampIds:
                yield prefix
    
    def getAllSets(self):
        return self._sets.keys()

    # private methods
    
    def _add(self, stamp, identifier, setSpecs, prefixes):
        for setSpec in setSpecs:
            self._sets.setdefault(setSpec,[]).append(stamp)
        for prefix in prefixes:
            self._prefixes.setdefault(prefix,[]).append(stamp)
        self._stamp2identifier[stamp]=identifier
        self._identifier2stamp[identifier]=stamp

    def _fromPredicate(self, oaiFrom):
        if not oaiFrom:
            return lambda stamp: False
        fromStamp = int(mktime(strptime(oaiFrom, '%Y-%m-%dT%H:%M:%SZ'))*1000000.0)
        return lambda stamp: stamp < fromStamp
    
    def _untilPredicate(self, oaiUntil):
        if not oaiUntil:
            return lambda stamp: True
        UNTIL_IS_INCLUSIVE = 1 # Add one second to 23:59:59
        untilStamp = int(mktime(strptime(oaiUntil, '%Y-%m-%dT%H:%M:%SZ'))*1000000.0) + UNTIL_IS_INCLUSIVE
        return lambda stamp: stamp < untilStamp
        
    def _delete(self, identifier):
        stamp = self._identifier2stamp.get(identifier, None)
        oldPrefixes = []
        oldSets = []
        if stamp != None:
            del self._identifier2stamp[identifier]
            del self._stamp2identifier[stamp]
            for prefix, prefixStamps in self._prefixes.items():
                if stamp in prefixStamps:
                    prefixStamps.remove(stamp)
                    oldPrefixes.append(prefix)
            for setSpec, setStamps in self._sets.items():
                if stamp in setStamps:
                    setStamps.remove(stamp)
                    oldSets.append(setSpec)
            if stamp in self._deleted:
                self._deleted.remove(stamp)
        return oldPrefixes, oldSets

    def _read(self):
        self._prefixes = {}
        for prefix in (name[:-len('.stamps')] for name in listdir(join(self._directory, 'prefixes')) if name.endswith('.stamps')):
            with open(join(self._directory, 'prefixes', '%s.stamps' % prefix)) as f:
                self._prefixes[unescapeName(prefix)] = [int(stamp.strip()) for stamp in f if stamp]
        self._sets = {}
        for setSpec in (name[:-len('.stamps')] for name in listdir(join(self._directory, 'sets')) if name.endswith('.stamps')):
            with open(join(self._directory, 'sets', '%s.stamps' % setSpec)) as f:
                self._sets[unescapeName(setSpec)] = [int(stamp.strip()) for stamp in f if stamp]
        self._stamp2identifier = {}
        self._identifier2stamp = {}
        identifiersFile = join(self._directory, 'identifiers')
        if isfile(identifiersFile):
            with open(identifiersFile) as f:
                for stamp, identifier in (line.strip().split(' ',1) for line in f):
                    self._stamp2identifier[int(stamp)] = identifier
                    self._identifier2stamp[identifier] = int(stamp)
        deletedFile = join(self._directory, 'deleted')
        if isfile(deletedFile):
            with open(deletedFile) as f:
                self._deleted = set(int(stamp.strip()) for stamp in f if stamp.strip())

    def _store(self, metadataFormats=[]):
        for prefix, stamps in self._prefixes.items():
            _writeLines(join(self._directory, 'prefixes', '%s.stamps' % escapeName(prefix)), stamps)
        for setSpec, stamps in self._sets.items():
            _writeLines(join(self._directory, 'sets', '%s.stamps' % escapeName(setSpec)), stamps)
        _writeLines(join(self._directory, 'identifiers'), ('%s %s' % (k,v) for k,v in self._stamp2identifier.items()))
        _writeLines(join(self._directory, 'deleted'), self._deleted)
        for prefix, schema, namespace in metadataFormats:
            _write(join(self._directory, 'prefixes', '%s.schema' % escapeName(prefix)), schema)
            _write(join(self._directory, 'prefixes', '%s.namespace' % escapeName(prefix)), namespace)

    def _stamp(self):
        """time in microseconds"""
        return int(time()*1000000.0)

# helper methods

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
    