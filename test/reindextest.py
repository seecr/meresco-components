# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
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

from cq2utils import CQ2TestCase, CallTrace
from meresco.components import StorageComponent, Reindex, FilterMessages
from meresco.core import Observable, fakeGenerator
from lxml.etree import tostring
from escaping import unescapeFilename, escapeFilename

from os.path import join, isdir
from os import listdir
from weightless.core import compose, be

class ReindexTest(CQ2TestCase):
    def _path(self, subdir):
        return join(self.tempdir, subdir)

    def setupStorage(self, records):
        storage = StorageComponent(self._path('storage'))
        for record in records:
            storage.add(**record)
        return storage

    def setupDna(self, storage):
        @fakeGenerator
        def addDocumentPart(**kwargs):
            pass
        observer = CallTrace('observer', methods={'addDocumentPart': addDocumentPart})
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
            result = list(compose(reindex.handleRequest(arguments=arguments)))
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
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))
        self.assertFalse(isdir(directory))
        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', "!error: no identifiers"], result)

    def testCreateIdentifierFiles(self):
        storage = self.setupStorage([
            dict(identifier='id:1', partname='part',  data='data1'),
            dict(identifier='id:2', partname='part', data='data2'),
            dict(identifier='id:3', partname='part', data='data3'),
        ])
        reindex, observer = self.setupDna(storage)
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))
        directory = join(self._path('reindex'), 'testcase')
        self.assertTrue(isdir(directory))
        files = listdir(directory)
        self.assertEquals(1, len(files))
        identifiers = sorted(list(identifier for identifier in open(join(directory, files[0])).read().split('\n') if identifier != ''))
        self.assertEquals(['id:1', 'id:2', 'id:3'], identifiers)

    def testCreateIdentifierFilesInBatches(self):
        storage = self.setupStorage([
            dict(identifier='id:1', partname='part',  data='data1'),
            dict(identifier='id:2', partname='part', data='data2'),
            dict(identifier='id:3', partname='part', data='data3'),
        ])
        reindex, observer = self.setupDna(storage)
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase'], 'batchsize': ['1']})))
        directory = join(self._path('reindex'), 'testcase')
        self.assertTrue(isdir(directory))
        files = listdir(directory)
        self.assertEquals(3, len(files))

    def testCreateIdentifierFilesYieldsOutput(self):
        storage = self.setupStorage([
            dict(identifier='id:1', partname='part',  data='data1'),
            dict(identifier='id:2', partname='part', data='data2'),
            dict(identifier='id:3', partname='part', data='data3'),
        ])
        reindex, observer = self.setupDna(storage)
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))

        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '#', '\n=batches: 1'], result)

    def testProcessCreatedBatches(self):
        storage = self.setupStorage([
            dict(identifier='id:1', partname='part',  data='data1'),
            dict(identifier='id:2', partname='part', data='data2'),
            dict(identifier='id:3', partname='part', data='data3'),
        ])
        reindex, observer = self.setupDna(storage)
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))

        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '#', '\n=batches: 1'], result)
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', result[0])
        self.assertEquals('=batches left: 0', result[-1])
        for i in ['+id:1\n', '+id:2\n', '+id:3\n' ]:
            self.assertTrue(i in result)

        self.assertEquals(['addDocumentPart']*3, [m.name for m in observer.calledMethods])
        self.assertEquals(['id:1','id:2','id:3'], sorted([m.kwargs['identifier'] for m in observer.calledMethods]))
        self.assertEquals(['ignoredName']*3, [m.kwargs['partname'] for m in observer.calledMethods])
        self.assertEquals(['<empty/>']*3, [tostring(m.kwargs['lxmlNode']) for m in observer.calledMethods])

    def testRemoveFilesAndDirectoryAfterProcess(self):
        storage = self.setupStorage([
            dict(identifier='id:1', partname='part',  data='data1'),
            dict(identifier='id:2', partname='part', data='data2'),
            dict(identifier='id:3', partname='part', data='data3'),
        ])
        reindex, observer = self.setupDna(storage)
        directory = join(self._path('reindex'), 'testcase')

        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase'], 'batchsize': ['1']})))
        self.assertEquals(3, len(listdir(directory)))
        self.assertTrue(isdir(directory))

        ids, batchesLeft = [], []
        status, idPart, batchesLeftPart = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))
        ids.append(idPart)
        batchesLeft.append(batchesLeftPart)
        self.assertEquals(2, len(listdir(directory)))
        self.assertTrue(isdir(directory))

        status, idPart, batchesLeftPart = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))
        ids.append(idPart)
        batchesLeft.append(batchesLeftPart)
        self.assertEquals(1, len(listdir(directory)))
        self.assertTrue(isdir(directory))

        status, idPart, batchesLeftPart = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))
        ids.append(idPart)
        batchesLeft.append(batchesLeftPart)
        self.assertFalse(isdir(directory))

        self.assertEquals(['+id:1\n', '+id:2\n', '+id:3\n'], sorted(ids))
        self.assertEquals(['=batches left: 0', '=batches left: 1', '=batches left: 2'], sorted(batchesLeft))

    def testProcessGivesError(self):
        storage = self.setupStorage([
            dict(identifier='id:1', partname='part',  data='data1'),
        ])
        reindex, observer = self.setupDna(storage)
        observer.exceptions['addDocumentPart'] = Exception('An Error Occured')
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))

        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '#', '\n=batches: 1'], result)
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))
        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '\n!error processing "id:1": An Error Occured'], result)

    def testNotOffByOneIfNoRemainder(self):
        records = [dict(identifier='id:%d' % i, partname='part', data='data%d' % i) for i in range(80)]
        storage = self.setupStorage(records)
        reindex, observer = self.setupDna(storage)
        directory = join(self._path('reindex'), 'testcase')
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase'], 'batchsize': ['5']})))
        self.assertEquals(16, len(listdir(directory)))
        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '\n=batches: 16'], result)

    def testProcessingBatchesIsAsynchronous(self):
        storage = self.setupStorage([
            dict(identifier='id:1', partname='part', data='data1'),
        ])
        reindex, observer = self.setupDna(storage)
        observer.returnValues['addDocumentPart'] = (f for f in [str])
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))
        self.assertTrue(str in result, result)
    
    def testBatchWithStrangeIdentifier(self):
        identifier = unescapeFilename("newline%0A >")
        storage = self.setupStorage([
            dict(identifier=identifier, partname='part', data='data1'),
        ])
        reindex, observer = self.setupDna(storage)
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))

        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '#', '\n=batches: 1'], result)
        result = list(compose(reindex.handleRequest(arguments={'session': ['testcase']})))
        self.assertEquals(['HTTP/1.0 200 OK\r\nContent-Type: plain/text\r\n\r\n', '+%s\n' % escapeFilename(identifier), '=batches left: 0'], result)

        self.assertEquals(['addDocumentPart'], [m.name for m in observer.calledMethods])
        self.assertEquals([identifier], [m.kwargs['identifier'] for m in observer.calledMethods])
        self.assertEquals(['ignoredName'], [m.kwargs['partname'] for m in observer.calledMethods])
        self.assertEquals(['<empty/>'], [tostring(m.kwargs['lxmlNode']) for m in observer.calledMethods])

