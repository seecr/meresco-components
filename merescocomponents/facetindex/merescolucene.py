# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco-Lucene is a Python binding for Lucene using CTypes
#    Copyright (C) 2009 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of Meresco-Lucene.
#
#    Meresco-Lucene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco-Lucene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco-Lucene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##


import sys
from os.path import join, abspath, dirname, isfile

import jtool
from jtool import JClass

if hasattr(jtool, "load"):
    jtool.load(join(abspath(dirname(__file__)), "_facetindex.so"))
    jtool.load('liblucene-core.so.2')
    MerescoJClass = type
else:
    facetIndexLibPath = join(abspath(dirname(__file__)), "_facetindex.so")
    assert(isfile(facetIndexLibPath))
    sys.path.extend([facetIndexLibPath, 'liblucene-core.so.2'])
    class MerescoJClass(JClass):
        def __new__(self, name, bases, dct):
            base = bases[0]
            kwargs = { 'jlib': base._jlib } if hasattr(base, '_jlib') else {}
            return JClass.__new__(self, name, bases, dct, jclassname=base.__name__, **kwargs)
        def __repr__(self):
            return 'Submetatype of ' + str(JClass)
        __str__ = __repr__


from java.lang import Object, Float
from java.lang.reflect import Array
from java.util import Iterator
import MerescoStandardAnalyzer
from ctypes import cdll, c_void_p

from org.apache.lucene.document import Fieldable, Field, Document as _Document
from org.apache.lucene.index import Term, IndexReader, IndexWriter as _IndexWriter, TermEnum
from org.apache.lucene.analysis import Analyzer
from org.apache.lucene.store import Directory, FSDirectory
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.search import TermQuery, Query, MatchAllDocsQuery, Sort, IndexSearcher as _IndexSearcher, Searcher, Hits as _Hits
from org.apache.lucene.search import BooleanClause, BooleanQuery, PhraseQuery, PrefixQuery

merescoStandardAnalyzer = MerescoStandardAnalyzer() % Analyzer

@staticmethod
def c_void_from_jparam(arg):
    return c_void_p(arg.jaddress())

def iterJ(jIterator):
    try:
        jIterator.hasNext()
    except AttributeError:
        try:
            jIterator = jIterator.iterator()
        except AttributeError:
            jarray = jIterator % Object
            for i in range(0, Array.getLength(jarray)):
                yield Array.get(jarray, i)
            return
    while jIterator.hasNext():
        yield jIterator.next()


class IndexWriter(_IndexWriter):
    __metaclass__ = MerescoJClass
    def __new__(clazz, directoryName, analyzer, create):
        directory = FSDirectory.getDirectory(directoryName) % Directory
        # autocommit = True
        return _IndexWriter.__new__(clazz, directory, True, analyzer % Analyzer, create)

    def __init__(self, directoryName, analyzer, create):
        self.setMaxBufferedDocs(10)
        self.setMergeFactor(10)

    def commit(self):
        self.flush() # Lucene 2.2/2.4 compatibility

    def numDocs(self):
        return self.docCount() # Lucene 2.2/2.4 compatibility

class Document(_Document):
    __metaclass__ = MerescoJClass
    def add(self, field):
        return _Document.add(self, field % Fieldable)

class IndexSearcher(_IndexSearcher):
    __metaclass__ = MerescoJClass
    def search(self, query, sort=None):
        if sort == None:
            return _IndexSearcher.search(self, query % Query)
        return _IndexSearcher.search(self, query % Query, sort)

for cls in [Field, Term, TermQuery, Query, MatchAllDocsQuery, Sort,
            IndexReader, IndexSearcher, Searcher, BooleanQuery,
            MerescoStandardAnalyzer, Analyzer, PhraseQuery, PrefixQuery,
            Field.Store, Field.Index]:
    cls.from_param = c_void_from_jparam


def asFloat(d):
    return Float.TYPE(jobj=Float(d).jaddress())
