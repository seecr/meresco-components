# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# 
# This file is part of "Meresco Components"
# 
# "Meresco Components" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Meresco Components" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Meresco Components"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from hashlib import sha1

from storage import HierarchicalStorage, Storage
from meresco.core import asyncnoreturnvalue

class DefaultStrategy(object):

    @classmethod
    def split(self, xxx_todo_changeme1):
        (identifier, partname) = xxx_todo_changeme1
        result = identifier.split(':',1)
        if partname != None:
            result += [partname]
        return result

    @classmethod
    def join(self, parts):
        identifier = ":".join(parts[:-1])
        partname = parts[-1]
        return identifier, partname

defaultSplit = DefaultStrategy.split
defaultJoin = DefaultStrategy.join

class HashDistributeStrategy(object):

    def split(self, xxx_todo_changeme2):
        (identifier, partname) = xxx_todo_changeme2
        hash = sha1(identifier).hexdigest()
        if partname is None:
            partname = ""
        return hash[0:2], hash[2:4], hash + '.' + partname

    def join(self, _):
        raise KeyError("Unable to join due to hashing of identifiers")

class StorageComponent(object):
    def __init__(self, directory, partsRemovedOnDelete=None, partsRemovedOnPurge=None, name=None, strategy=DefaultStrategy):
        assert type(directory) == str, 'Please use directory as first parameter'
        self._storage = HierarchicalStorage(Storage(directory), strategy.split, strategy.join)
        self._partsRemovedOnDelete = set([]) if partsRemovedOnDelete is None else set(partsRemovedOnDelete)
        self._partsRemovedOnPurge = self._partsRemovedOnDelete if partsRemovedOnPurge is None else self._partsRemovedOnDelete.union(set(partsRemovedOnPurge))
        self._name = name

    def observable_name(self):
        return self._name

    @asyncnoreturnvalue
    def add(self, identifier, partname, data):
        if not identifier:
            raise ValueError("Empty identifier is not allowed.")
        sink = self._storage.put((identifier, partname))
        try:
            sink.send(data)
        finally:
            sink.close()

    @asyncnoreturnvalue
    def delete(self, identifier):
        if not identifier:
            raise ValueError("Empty identifier is not allowed.")
        for partname in self._partsRemovedOnDelete:
            self.deletePart(identifier, partname)

    def deletePart(self, identifier, partname):
        if (identifier, partname) in self._storage:
            self._storage.delete((identifier, partname))

    def purge(self, identifier):
        if not identifier:
            raise ValueError("Empty identifier is not allowed.")
        for partname in self._partsRemovedOnPurge:
            if (identifier, partname) in self._storage:
                self._storage.purge((identifier, partname))

    def isAvailable(self, identifier, partname):
        """returns (hasId, hasPartName)"""
        if (identifier, partname) in self._storage:
            return True, True
        elif (identifier, None) in self._storage:
            return True, False
        return False, False

    def write(self, sink, identifier, partname):
        stream = self._storage.getFile((identifier, partname))
        try:
            for line in stream:
                sink.write(line)
        finally:
            stream.close()

    def yieldRecord(self, identifier, partname):
        stream = self._storage.getFile((identifier, partname))
        for data in stream:
            yield data
        stream.close()

    def getStream(self, identifier, partname):
        return self._storage.getFile((identifier, partname))

    def listIdentifiers(self, partname=None, identifierPrefix=''):
        return (identifier for identifier, ignored in self.glob((identifierPrefix, partname)))

    def glob(self, xxx_todo_changeme3):
        (prefix, wantedPartname) = xxx_todo_changeme3
        def filterPrefixAndPart(xxx_todo_changeme):
            (identifier, partname) = xxx_todo_changeme
            return identifier.startswith(prefix) and (wantedPartname == None or wantedPartname == partname)

        return ((identifier, partname) for (identifier, partname) in self._storage.glob((prefix, wantedPartname))
                if filterPrefixAndPart((identifier, partname)))

