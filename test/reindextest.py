# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from cq2utils import CQ2TestCase, CallTrace
from meresco.components import StorageComponent, Reindex, FilterMessages
from meresco.core import be, Observable

from os.path import join, isdir
from os import listdir

class ReindexTest(CQ2TestCase):
    def _path(self, subdir):
        return join(self.tempdir, subdir)

    def setupStorage(self, records):
        storage = StorageComponent(self._path('storage'))
        for record in records:
            storage.add(*record)
        return storage

    def setupDna(self, storage):
        observer = CallTrace('observer')
        reindex = be(
            (Reindex(filelistPath=self._path('reindex'), partName='part'),
                (FilterMessages(allowed=['listIdentifiers']),
                    (storage, ),
                ),
                (observer,)
            )
        )
        return reindex, observer

    def testArguments(self):
        reindex, observer = self.setupDna(CallTrace('Storage'))
        def assertError(message, arguments):
            result = list(reindex.handleRequest(arguments=arguments))
            self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', message], result)
        assertError('!error: session missing', {})
        assertError('!error: session missing', {'session': []})

        assertError('!error: invalid batchsize', {'session': ['test'], 'batchsize': ['-1']})
        assertError('!error: invalid batchsize', {'session': ['test'], 'batchsize': ['0']})
        assertError('!error: invalid batchsize', {'session': ['test'], 'batchsize': ['2001']})

    def testWithEmptyStorage(self):
        reindex, observer = self.setupDna(CallTrace('Storage', returnValues={'listIdentifiers': []}))
        directory = join(self._path('reindex'), 'testcase')
        self.assertFalse(isdir(directory))
        result = list(reindex.handleRequest(arguments={'session': ['testcase']}))
        self.assertFalse(isdir(directory))
        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', "!error: no identifiers"], result)

    def testCreateIdentifierFiles(self):
        storage = self.setupStorage([
            ('id:1', 'part', 'data1'),
            ('id:2', 'part', 'data2'),
            ('id:3', 'part', 'data3'),
        ])
        reindex, observer = self.setupDna(storage)
        result = list(reindex.handleRequest(arguments={'session': ['testcase']}))
        directory = join(self._path('reindex'), 'testcase')
        self.assertTrue(isdir(directory))
        files = listdir(directory)
        self.assertEquals(1, len(files))
        identifiers = list(identifier for identifier in open(join(directory, files[0])).read().split('\n') if identifier != '')
        self.assertEquals(['id:1', 'id:2', 'id:3'], identifiers)

    def testCreateIdentifierFilesInBatches(self):
        storage = self.setupStorage([
            ('id:1', 'part', 'data1'),
            ('id:2', 'part', 'data2'),
            ('id:3', 'part', 'data3'),
        ])
        reindex, observer = self.setupDna(storage)
        result = list(reindex.handleRequest(arguments={'session': ['testcase'], 'batchsize': ['1']}))
        directory = join(self._path('reindex'), 'testcase')
        self.assertTrue(isdir(directory))
        files = listdir(directory)
        self.assertEquals(3, len(files))

    def testCreateIdentifierFilesYieldsOutput(self):
        storage = self.setupStorage([
            ('id:1', 'part', 'data1'),
            ('id:2', 'part', 'data2'),
            ('id:3', 'part', 'data3'),
        ])
        reindex, observer = self.setupDna(storage)
        result = list(reindex.handleRequest(arguments={'session': ['testcase']}))

        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '#', '\n=batches: 1'], result)

    def testProcessCreatedBatches(self):
        storage = self.setupStorage([
            ('id:1', 'part', 'data1'),
            ('id:2', 'part', 'data2'),
            ('id:3', 'part', 'data3'),
        ])
        reindex, observer = self.setupDna(storage)
        result = list(reindex.handleRequest(arguments={'session': ['testcase']}))

        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '#', '\n=batches: 1'], result)
        result = list(reindex.handleRequest(arguments={'session': ['testcase']}))
        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '+id:1\n', '+id:2\n', '+id:3\n', '=batches left: 0'], result)

        methods = [str(m) for m in observer.calledMethods]
        self.assertEquals(3, len(methods))
        self.assertEquals("addDocumentPart(identifier='id:1', name='ignoredName', lxmlNode=<etree._ElementTree>)", methods[0])
        self.assertEquals("addDocumentPart(identifier='id:2', name='ignoredName', lxmlNode=<etree._ElementTree>)", methods[1])
        self.assertEquals("addDocumentPart(identifier='id:3', name='ignoredName', lxmlNode=<etree._ElementTree>)", methods[2])

    def testRemoveFilesAndDirectoryAfterProcess(self):
        storage = self.setupStorage([
            ('id:1', 'part', 'data1'),
            ('id:2', 'part', 'data2'),
            ('id:3', 'part', 'data3'),
        ])
        reindex, observer = self.setupDna(storage)
        directory = join(self._path('reindex'), 'testcase')

        result = list(reindex.handleRequest(arguments={'session': ['testcase'], 'batchsize': ['1']}))
        self.assertEquals(3, len(listdir(directory)))
        self.assertTrue(isdir(directory))

        result = list(reindex.handleRequest(arguments={'session': ['testcase']}))
        self.assertEquals(2, len(listdir(directory)))
        self.assertTrue(isdir(directory))
        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '+id:1\n', '=batches left: 2'], result)

        result = list(reindex.handleRequest(arguments={'session': ['testcase']}))
        self.assertEquals(1, len(listdir(directory)))
        self.assertTrue(isdir(directory))
        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '+id:2\n', '=batches left: 1'], result)

        result = list(reindex.handleRequest(arguments={'session': ['testcase']}))
        self.assertFalse(isdir(directory))
        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '+id:3\n','=batches left: 0'], result)

    def testProcessGivesError(self):
        storage = self.setupStorage([
            ('id:1', 'part', 'data1'),
            ('id:2', 'part', 'data2'),
            ('id:3', 'part', 'data3'),
        ])
        reindex, observer = self.setupDna(storage)
        observer.exceptions['addDocumentPart'] = Exception('An Error Occured')
        result = list(reindex.handleRequest(arguments={'session': ['testcase']}))

        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '#', '\n=batches: 1'], result)
        result = list(reindex.handleRequest(arguments={'session': ['testcase']}))
        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '\n!error processing "id:1": An Error Occured'], result)

    def testNotOffByOneIfNoRemainder(self):
        records = [('id:%d' % i, 'part', 'data%d' % i) for i in range(80)]
        storage = self.setupStorage(records)
        reindex, observer = self.setupDna(storage)
        directory = join(self._path('reindex'), 'testcase')
        result = list(reindex.handleRequest(arguments={'session': ['testcase'], 'batchsize': ['5']}))
        self.assertEquals(16, len(listdir(directory)))
        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '\n=batches: 16'], result)
