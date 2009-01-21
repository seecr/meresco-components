
from lucene import IncludeStopWordAnalyzer
from PyLucene import IndexReader, IndexWriter, IndexSearcher, Document as LuceneDocument, Field, TermQuery, Term, MatchAllDocsQuery

class LuceneDict(object):
    def __init__(self, directoryName):
        self._directoryName = directoryName
        self._writer = None
        self._reader = None
        self._searcher = None
        self._reopenIndex()
        
    def _reopenIndex(self):
        if self._writer:
            self._writer.close()
        self._writer = IndexWriter(
            self._directoryName,
            IncludeStopWordAnalyzer(), not IndexReader.indexExists(self._directoryName))
        if self._reader:
            self._reader.close()
        self._reader = IndexReader.open(self._directoryName)
        if self._searcher:
            self._searcher.close()
        self._searcher = IndexSearcher(self._reader)

    def __setitem__(self, key, value):
        item = LuceneDocument()
        item.add(Field('key', key, Field.Store.YES, Field.Index.UN_TOKENIZED))
        item.add(Field('value', value, Field.Store.YES, Field.Index.UN_TOKENIZED))
        self._writer.deleteDocuments(Term('key', key))
        self._writer.addDocument(item)
        self._reopenIndex()

    def __getitem__(self, key):
        hits = self._searcher.search(TermQuery(Term('key', key)))
        if len(hits) != 1:
            raise KeyError(key)
        return hits.doc(0).getField('value').stringValue()

    def __delitem__(self, key):
        self._writer.deleteDocuments(Term('key', key))
        self._reopenIndex()

    def __contains__(self, key):
        return len(self._searcher.search(TermQuery(Term('key', key)))) == 1

    def __len__(self):
        return self._reader.numDocs()

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
        hits = self._searcher.search(MatchAllDocsQuery())
        for i in xrange(len(hits)):
            yield (hits.doc(i).getField('key').stringValue(), hits.doc(i).getField('value').stringValue())

    def keys(self):
        return (key for key,value in self.items())

    def values(self):
        return (value for key,value in self.items())
    