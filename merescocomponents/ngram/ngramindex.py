# -*- coding: utf-8 -*-

from merescocore.framework import Observable
from merescocomponents.facetindex import Document
from ngram import ngrams, NGRAMS_FIELD, NAME_FIELD, IDENTIFIER_TEMPLATE, NAME_TEMPLATE

from string import punctuation

def tokenize(value):
    for word in unicode(value).split():
        word = word.strip(punctuation)
        if len(word) > 1:
            yield word.lower()

class NGramIndex(Observable):
    def __init__(self, transactionName, N=2, fieldnames=None):
        Observable.__init__(self)
        self._fieldnames = set(fieldnames) if fieldnames else set()
        self._transactionName = transactionName
        self._N = N

    def begin(self):
        if self.ctx.tx.name == self._transactionName:
            self.ctx.tx.join(self)
            self._values = set()

    def addField(self, name, value):
        for word in tokenize(value):
            self._values.add(IDENTIFIER_TEMPLATE % (word,''))
            if name in self._fieldnames:
                self._values.add(IDENTIFIER_TEMPLATE % (word, name))

    def commit(self):
        for value in self._values:
            word, name = value.rsplit('$', 1)
            doc = Document(value)
            doc.addIndexedField(NGRAMS_FIELD, ' '.join(ngrams(word, self._N)))
            doc.addIndexedField(NAME_FIELD, NAME_TEMPLATE % name, tokenize=False)
            self.do.addDocument(doc)
        
        
