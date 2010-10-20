# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
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

from storage import HierarchicalStorage, Storage
from itertools import ifilter

def defaultSplit((identifier, partname)):
    result = identifier.split(':',1)
    if partname != None:
        result += [partname]
    return result

def defaultJoin(parts):
    identifier = ":".join(parts[:-1])
    partname = parts[-1]
    return identifier, partname

class StorageComponent(object):
    def __init__(self, directory, split=defaultSplit, join=defaultJoin, revisionControl=False, partsRemovedOnDelete=[], name=None):
        assert type(directory) == str, 'Please use directory as first parameter'
        self._storage = HierarchicalStorage(Storage(directory, revisionControl=revisionControl, ), split, join)
        self._partsRemovedOnDelete = partsRemovedOnDelete
        self._name = name

    def observable_name(self):
        return self._name

    def store(self, *args, **kwargs):
        return self.add(*args, **kwargs)

    def addDocumentPart(self, identifier=None, partname=None, data=None):
        return self.add(identifier=identifier, partname=partname, data=data)

    def add(self, identifier, partname, data):
        """should be obsoleted in favor of addDocumentPart"""
        sink = self._storage.put((identifier, partname))
        try:
            sink.send(data)
        finally:
            return sink.close()

    def delete(self, identifier):
        for partname in self._partsRemovedOnDelete:
            self.deletePart(identifier, partname)

    def deletePart(self, identifier, partname):
        if (identifier, partname) in self._storage:
            self._storage.delete((identifier, partname))

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

    def _listIdentifiers(self, identifierPrefix=''):
        lastIdentifier = None
        for identifier, partname in self.glob((identifierPrefix, None)):
            if identifier != lastIdentifier:
                yield identifier
                lastIdentifier = identifier

    def _listIdentifiersByPartName(self, partname, identifierPrefix=''):
        for identifier, ignored in self.glob((identifierPrefix, partname)):
            yield identifier

    def listIdentifiers(self, partname=None, identifierPrefix=''):
        """Use an ifilter to hide the generator so it won't be consumed by compose"""
        return ifilter(None, self._listIdentifiersByPartName(partname, identifierPrefix=identifierPrefix))

    def glob(self, (prefix, wantedPartname)):
        def filterPrefixAndPart((identifier, partname)):
            return identifier.startswith(prefix) and (wantedPartname == None or wantedPartname == partname)

        return ifilter(filterPrefixAndPart, self._storage.glob((prefix, wantedPartname)))
