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
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase

from meresco.components.storagecomponent import StorageComponent, DefaultStrategy, HashDistributeStrategy
from storage import HierarchicalStorage, Storage
from io import StringIO
from meresco.core import Observable
from subprocess import Popen, PIPE
from weightless.core import compose
from os.path import join


class StorageComponentTest(SeecrTestCase):

    def setUp(self):
        SeecrTestCase.setUp(self)

        self.storageComponent = StorageComponent(self.tempdir)
        self.storage = self.storageComponent._storage

    def testAdd(self):
        list(compose(self.storageComponent.add("id_0", "partName", "The contents of the part")))
        self.assertEqual('The contents of the part', self.storage.get(('id_0', 'partName')).read())

    def testAddEmptyIdentifier(self):
        self.assertRaises(ValueError, lambda: list(compose(self.storageComponent.add("", "part", "data"))))
        self.assertRaises(ValueError, lambda: list(compose(self.storageComponent.add(None, "part", "data"))))

    def testDeleteEmptyIdentifier(self):
        self.assertRaises(ValueError, lambda: list(compose(self.storageComponent.delete(""))))
        self.assertRaises(ValueError, lambda: list(compose(self.storageComponent.delete(None))))
        self.storageComponent.deletePart("","part")

    def testIsAvailableIdAndPart(self):
        sink = self.storage.put(('some:thing:anId-123','somePartName'))
        sink.send('read string')
        sink.close()

        hasId, hasPartName = self.storageComponent.isAvailable("some:thing:anId-123", "somePartName")
        self.assertTrue(hasId)
        self.assertTrue(hasPartName)

    def testIsAvailableId(self):
        sink = self.storage.put(('some:thing:anId-123','somePartName.xml'))
        sink.send('read string')
        sink.close()

        hasId, hasPartName = self.storageComponent.isAvailable("some:thing:anId-123", "nonExistingPart")
        self.assertTrue(hasId)
        self.assertFalse(hasPartName)

    def testIsNotAvailable(self):
        hasId, hasPartName = self.storageComponent.isAvailable("some:thing:anId-123", "nonExistingPart")
        self.assertFalse(hasId)
        self.assertFalse(hasPartName)

    def testWrite(self):
        sink = self.storage.put(('some:thing:anId-123','somePartName'))
        sink.send('read string')
        sink.close()
        stream = StringIO()
        self.storageComponent.write(stream, "some:thing:anId-123", "somePartName")
        self.assertEqual('read string', stream.getvalue())

    def testDeleteParts(self):
        identifier = ('some:thing:anId-123','somePartName')
        self.storage.put(identifier).close()
        self.assertTrue(identifier in self.storage)
        self.storageComponent.deletePart('some:thing:anId-123', 'somePartName')
        self.assertFalse(identifier in self.storage)

    def testDelete(self):
        identifier = ('some:thing:anId-123','somePartName')
        self.storage.put(identifier).close()
        self.assertTrue(identifier in self.storage)
        list(compose(self.storageComponent.delete('some:thing:anId-123')))
        self.assertTrue(identifier in self.storage)

        self.storageComponent = StorageComponent(self.tempdir, partsRemovedOnDelete=['somePartName'])
        self.storage = self.storageComponent._storage
        list(compose(self.storageComponent.delete('some:thing:anId-123')))
        self.assertFalse(identifier in self.storage)

    def testPurgeWithoutIdentifierNotAllowed(self):
        self.assertRaises(ValueError, lambda: StorageComponent(self.tempdir).purge(''))

    def testPurge(self):
        identifier = ('some:thing:anId-123','somePartName')
        self.storage.put(identifier).close()
        self.assertTrue(identifier in self.storage)
        self.storageComponent.purge('some:thing:anId-123')
        self.assertTrue(identifier in self.storage)

        self.storageComponent = StorageComponent(self.tempdir, partsRemovedOnDelete=['somePartName'])
        self.storage = self.storageComponent._storage
        self.storageComponent.purge('some:thing:anId-123')
        self.assertFalse(identifier in self.storage)

        self.storageComponent = StorageComponent(self.tempdir, partsRemovedOnDelete=['somePartName'], partsRemovedOnPurge=['notTherePart'])
        self.storage = self.storageComponent._storage
        self.storageComponent.purge('some:thing:anId-123')
        self.assertFalse(identifier in self.storage)

    def testDeleteNonexisting(self):
        identifier = ('some:thing:anId-123','somePartName.xml')
        self.assertFalse(identifier in self.storage)
        self.storageComponent.deletePart('some:thing:anId-123', 'somePartName')
        self.assertFalse(identifier in self.storage)

    def testEnumerate(self):
        self.assertEqual(set([]), set(self.storageComponent.listIdentifiers()))
        list(compose(self.storageComponent.add('some:thing:anId-123','somePartName', 'data')))
        self.assertEqual(set(['some:thing:anId-123']), set(self.storageComponent.listIdentifiers()))
        list(compose(self.storageComponent.add('some:thing:anId-123','anotherPartName', 'data')))
        self.assertEqual(set(['some:thing:anId-123']), set(self.storageComponent.listIdentifiers()))
        list(compose(self.storageComponent.add('some:thing:anId-122','anotherPartName', 'data')))
        list(compose(self.storageComponent.add('any:thing:anId-123','somePartName', 'data')))
        self.assertEqual(set(['some:thing:anId-123', 'some:thing:anId-122', 'any:thing:anId-123']), set(self.storageComponent.listIdentifiers()))
        self.assertEqual(set(['some:thing:anId-123', 'any:thing:anId-123']), set(self.storageComponent.listIdentifiers('somePartName')))

    def testGlob(self):
        self.assertEqual(set([]), set(self.storageComponent.glob(('some:thing:anId-123', None))))

        list(compose(self.storageComponent.add('some:thing:anId-123','somePartName', 'data')))
        self.assertEqual(set([('some:thing:anId-123', 'somePartName')]), set(self.storageComponent.glob(('so', None))))
        self.assertEqual(set([('some:thing:anId-123', 'somePartName')]), set(self.storageComponent.glob(('some', None))))
        self.assertEqual(set([('some:thing:anId-123', 'somePartName')]), set(self.storageComponent.glob(('some:thing', None))))
        self.assertEqual(set([('some:thing:anId-123', 'somePartName')]), set(self.storageComponent.glob(('some:thing:anId', None))))

        list(compose(self.storageComponent.add('some:thing:anId-123','anotherPartName', 'data')))
        self.assertEqual(set([('some:thing:anId-123', 'anotherPartName'), ('some:thing:anId-123', 'somePartName')]), set(self.storageComponent.glob(('some:thing:anId', None))))

        list(compose(self.storageComponent.add('some:thing:anId-124','anotherPartName', 'data')))
        self.assertEqual(set([('some:thing:anId-123', 'anotherPartName'), ('some:thing:anId-123', 'somePartName')]), set(self.storageComponent.glob(('some:thing:anId-123', None))))
        self.assertEqual(set([('some:thing:anId-123', 'somePartName')]), set(self.storageComponent.glob(('some:thing:anId-123', 'somePartName'))))

        self.assertEqual(set([('some:thing:anId-123', 'anotherPartName'), ('some:thing:anId-124', 'anotherPartName')]), set(self.storageComponent.glob(('some:thing:anId', 'anotherPartName'))))

        list(compose(self.storageComponent.add('some:thing:else-1','anotherPartName', 'data')))
        self.assertEqual(set([('some:thing:anId-123', 'anotherPartName'), ('some:thing:anId-124', 'anotherPartName')]), set(self.storageComponent.glob(('some:thing:anId', 'anotherPartName'))))

    def testObservableNameNotSet(self):
        s = StorageComponent(self.tempdir)
        self.assertEqual(None, s.observable_name())

    def testObservableNameSet(self):
        s = StorageComponent(self.tempdir, name="name")
        self.assertEqual("name", s.observable_name())

    def testDirectoryStrategy(self):
        class TestStrategy:
            @classmethod
            def split(self, xxx_todo_changeme):
                (identifier, partname) = xxx_todo_changeme
                return identifier.swapcase(), partname.swapcase()
            join = None
        s = StorageComponent(self.tempdir, strategy=TestStrategy)
        list(compose(s.add("AnIdentifier", "Part1", "Contents")))
        self.assertEqual("Contents", open(join(self.tempdir, "aNiDENTIFIER", "pART1")).read())

    def testDirectorySplit(self):
        class TestStrategy:
            @classmethod
            def split(self, xxx_todo_changeme1):
                (identifier, partname) = xxx_todo_changeme1
                return tuple(c for c in identifier) + (partname,)
            join = None
        s = StorageComponent(self.tempdir, strategy=TestStrategy)
        list(compose(s.add("id09", "Part1", "Contents")))
        self.assertEqual("Contents", open(join(self.tempdir, "i", "d", "0", "9", "Part1")).read())

    def testDirectoryStrategyJoin(self):
        class TestStrategy:
            @classmethod
            def split(self, xxx_todo_changeme2):
                (identifier, partname) = xxx_todo_changeme2
                result = tuple(c for c in identifier)
                return result if not partname else result + (partname,)
            @classmethod
            def join(self, parts):
                return ''.join(parts[:-1]), parts[-1]
        s = StorageComponent(self.tempdir, strategy=TestStrategy)
        list(compose(s.add("id09", "Part1", "Contents")))
        self.assertEqual(["id09"], list(s.listIdentifiers()))

    def testDefaultStrategy(self):
        s = DefaultStrategy
        self.assertEqual(["a", "b", "c"], s.split(("a:b", "c")))
        self.assertEqual(("a:b", "c"), s.join(("a", "b", "c")))
        self.assertEqual(["a", "b"], s.split(("a:b", None)))
        self.assertEqual(["a", "b:c", "d"], s.split(("a:b:c", "d")))
        self.assertEqual(("a:b:c", "d"), s.join(("a", "b:c", "d")))

    def testDefaultStrategyIsDefaultStrategy(self):
        s = StorageComponent(self.tempdir)
        list(compose(s.add("a:b:c", "d", "Hi")))
        self.assertEqual("Hi", open(join(self.tempdir, "a", "b:c", "d")).read())

    def testHashDistributeStrategy(self):
        s = HashDistributeStrategy()
        self.assertEqual(("58", "eb", "58eb8a535f07b1f7b94cd6083e664137301048a7.rdf"), s.split(("AnIdentifier", "rdf")))
        self.assertEqual(("58", "eb", "58eb8a535f07b1f7b94cd6083e664137301048a7.xml"), s.split(("AnIdentifier", "xml")))
        self.assertEqual(("35", "6a", "356a192b7913b04c54574d18c28d46e6395428ab."), s.split(("1", "")))
        self.assertEqual(("35", "6a", "356a192b7913b04c54574d18c28d46e6395428ab."), s.split(("1", None)))

        self.assertRaises(KeyError, lambda: s.join("NA"))
