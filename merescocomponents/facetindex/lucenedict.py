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

from PyLucene import IndexReader, IndexWriter, IndexSearcher, Document as LuceneDocument, Field, TermQuery, Term, MatchAllDocsQuery
from tools import unlock

class LuceneDict(object):
    def __init__(self, directoryName):
        self._directoryName = directoryName
        unlock(self._directoryName)
        self._writer = IndexWriter(directoryName, None, not IndexReader.indexExists(directoryName))
        self._searcher = IndexSearcher(directoryName)
        self._dirty = False

    def getSearcher(self):
        if self._dirty:
            self._writer.flush()
            self._searcher.close()
            self._searcher = IndexSearcher(self._directoryName)
            self._dirty = False
        return self._searcher

    def close(self):
        self._writer.close()
        self._searcher.close()
        self._writer = None
        self._searcher = None

    def __setitem__(self, key, value):
        item = LuceneDocument()
        item.add(Field('key', key, Field.Store.YES, Field.Index.UN_TOKENIZED))
        item.add(Field('value', value, Field.Store.YES, Field.Index.UN_TOKENIZED))
        self._writer.deleteDocuments(Term('key', key))
        self._writer.addDocument(item)
        self._dirty = True

    def __getitem__(self, key):
        hits = self.getSearcher().search(TermQuery(Term('key', key)))
        if len(hits) != 1:
            raise KeyError(key)
        return hits.doc(0).getField('value').stringValue()

    def __delitem__(self, key):
        self._writer.deleteDocuments(Term('key', key))
        self._dirty = True

    def __contains__(self, key):
        return len(self.getSearcher().search(TermQuery(Term('key', key)))) == 1

    def has_key(self, key):
        return key in self

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

    def items(self):
        hits = self.getSearcher().search(MatchAllDocsQuery())
        for i in xrange(len(hits)):
            yield (hits.doc(i).getField('key').stringValue(), hits.doc(i).getField('value').stringValue())

    def keys(self):
        return (key for key,value in self.items())

    def values(self):
        return (value for key,value in self.items())

    def getKeysFor(self, value):
        hits = self.getSearcher().search(TermQuery(Term('value', value)))
        return [hits.doc(i).getField('key').stringValue() for i in range(len(hits))]
