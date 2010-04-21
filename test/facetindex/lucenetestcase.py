#!/usr/local/bin/python
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

from merescocomponents.facetindex.merescolucene import IndexReader, IndexSearcher, IndexWriter, Document, Term, Field, Fieldable, merescoStandardAnalyzer, MatchAllDocsQuery

from cq2utils import CQ2TestCase
from merescocomponents.facetindex import DocSet
from os.path import join, isdir
from os import getlogin
from tempfile import gettempdir

class LuceneTestCase(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.matchAllDocsQuery = MatchAllDocsQuery()

    def createSimpleIndexWithEmptyDocuments(self, size):
        index = IndexWriter(self.tempdir, merescoStandardAnalyzer, True)
        for i in xrange(size):
            index.addDocument(Document())
        index.close()
        self.reader = IndexReader.open(self.tempdir)
        self.searcher = IndexSearcher(self.reader % IndexReader)

    def addToIndexWithFixedFieldAndValueDoc(self, field, value, size):
        index = IndexWriter(self.tempdir, merescoStandardAnalyzer, False)
        self._addDocuments(index, field, value, size)

    def createIndexWithFixedFieldAndValueDoc(self, field, value, size):
        index = IndexWriter(self.tempdir, merescoStandardAnalyzer, True)
        self._addDocuments(index, field, value, size)

    def _addDocuments(self, index, field, value, size):
        doc = Document()
        doc.add(Field(field, value, Field.Store.NO, Field.Index.UN_TOKENIZED) % Fieldable)
        for i in xrange(size):
            index.addDocument(doc)
        index.close()
        self.reader = IndexReader.open(self.tempdir)
        self.searcher = IndexSearcher(self.reader % IndexReader)

    def createBigIndex(self, size, valuemax=1000, log=False, indexName=None):
        def create(directory):
            from random import randint
            index = IndexWriter(directory, merescoStandardAnalyzer, True)
            for i in xrange(size):
                if log and i % 1000 == 0: print i
                doc = Document()
                for i in xrange(10):
                    doc.add(Field('field%d' % i, 't€rm'+str(randint(0, valuemax)),
                        Field.Store.NO, Field.Index.UN_TOKENIZED) % Fieldable)
                index.addDocument(doc)
            index.close()
        directory = self.getDir(indexName)
        if not IndexReader.indexExists(directory):
            create(directory)
        self.reader = IndexReader.open(directory)
        self.searcher = IndexSearcher(self.reader % IndexReader)

    def getDir(self, indexName):
        if indexName:
            return join(gettempdir(), 'meresco-components-%s' % getlogin(), indexName) 
        return self.tempdir
        
