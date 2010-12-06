# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009-2010 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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

from collections import defaultdict
from merescolucene import Document as LuceneDocument, Field, Fieldable, iterJ, asFloat, merescoStandardAnalyzer

from java.io import StringReader, Reader


def _pyAddToIndexWith(indexWriter, identifier, values):
    document = LuceneDocument()
    document.add(Field(IDFIELD, identifier, Field.Store.YES, Field.Index.UN_TOKENIZED) % Fieldable)
    for key, value, tokenize in values:
        document.add(Field(
                key,
                value,
                Field.Store.NO,
                Field.Index.TOKENIZED if tokenize else Field.Index.UN_TOKENIZED
            ) % Fieldable)
    indexWriter.addDocument(document)
    return document

try:
    from lucenegcjutil import addToIndexWith
except:
    addToIndexWith = _pyAddToIndexWith


IDFIELD = '__id__'

def tokenize(aString):
    ts = merescoStandardAnalyzer.tokenStream('ignored fieldname', StringReader(unicode(aString)) % Reader)
    tokens = []
    token = ts.next()
    while token != None:
        tokens.append(token.termText())
        token = ts.next()
    return tokens

class DocumentException(Exception):
    """Generic Document Exception"""
    pass

class Document(object):

    def __init__(self, anId):
        self.identifier = anId
        if not self._isValidFieldValue(anId):
            raise DocumentException("Invalid ID: '%s'" % anId)
        self._fields = []
        self._tokenize = tokenize

    def _isValidFieldValue(self, anObject):
        return isinstance(anObject, basestring) and anObject.strip()

    def fields(self):
        return [IDFIELD] + [key for key, value, tokenize in self._fields]

    def _validFieldName(self, aKey):
        return self._isValidFieldValue(aKey) and aKey.lower() != IDFIELD

    def addIndexedField(self, aKey, aValue, tokenize = True):
        if not self._validFieldName(aKey):
            raise DocumentException('Invalid fieldname: "%s"' % aKey)

        if not self._isValidFieldValue(aValue):
            return

        self._fields.append((aKey, aValue, tokenize))

    def addToIndexWith(self, anIndexWriter):
        return addToIndexWith(anIndexWriter, self.identifier, self._fields)

    def validate(self):
        if self._fields == []:
            raise DocumentException('Empty document')

    def asDict(self):
        return DocDict(self.fields, self._valuesForField)

    def _valuesForField(self, key):
        if key == IDFIELD:
            yield self.identifier
            return
        for fieldname, value, tokenize in self._fields:
            if fieldname == key:
                if tokenize:
                    for v in self._tokenize(value):
                        yield v
                else:
                    yield value

def unique(iterable):
    seen = set()
    for item in iterable:
        if item not in seen:
            seen.add(item)
            yield item


class DocDict(object):
    def __init__(self, keysMethod, valuesMethod):
        self._valuesMethod = lambda key: unique(valuesMethod(key))
        self.keys = lambda: set(keysMethod())

    def __cmp__(self, other):
        return cmp(dict(self.items()), other)

    def __getitem__(self, key, default=None):
        if not key in self.keys():
            return default
        return list(self._valuesMethod(key))
    get = __getitem__

    def items(self):
        return ((key, self[key]) for key in self.keys())

