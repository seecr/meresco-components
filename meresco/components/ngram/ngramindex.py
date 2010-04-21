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

from meresco.core import Observable
from meresco.components.facetindex import Document
from ngram import ngrams, NGRAMS_FIELD, NAME_FIELD, IDENTIFIER_TEMPLATE, NAME_TEMPLATE

from string import punctuation

def tokenize(value):
    for word in value.split():
        word = word.strip(punctuation)
        if len(word) > 1:
            yield word.lower()

class NGramIndex(Observable):
    def __init__(self, transactionName, N=2, fieldnames=None):
        Observable.__init__(self)
        self._fieldnames = set(unicode(fieldname) for fieldname in fieldnames) if fieldnames else set()
        self._transactionName = transactionName
        self._N = N

    def begin(self):
        if self.ctx.tx.name == self._transactionName:
            self.ctx.tx.join(self)
            self._values = set()

    def addField(self, name, value):
        name = unicode(name)
        value = unicode(value)
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
        
        
