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

import PyLucene

IDFIELD = '__id__'

class DocumentException(Exception):
    """Generic Document Exception"""
    pass

class Document(object):

    def __init__(self, anId):
        self.identifier = anId
        if not self._isValidFieldValue(anId):
            raise DocumentException("Invalid ID: '%s'" % anId)

        self._document = PyLucene.Document()
        self._document.add(PyLucene.Field(IDFIELD, anId, PyLucene.Field.Store.YES, PyLucene.Field.Index.UN_TOKENIZED))
        self._fields = [IDFIELD]

    def _isValidFieldValue(self, anObject):
        return isinstance(anObject, basestring) and anObject.strip()

    def fields(self):
        return self._fields

    def _validFieldName(self, aKey):
        return self._isValidFieldValue(aKey) and aKey.lower() != IDFIELD

    def addIndexedField(self, aKey, aValue, tokenize = True):
        if not self._validFieldName(aKey):
            raise DocumentException('Invalid fieldname: "%s"' % aKey)

        if not self._isValidFieldValue(aValue):
            return

        self._addIndexedField(aKey, aValue, tokenize)
        self._fields.append(aKey)

    def _addIndexedField(self, aKey, aValue, tokenize = True):
        self._document.add(PyLucene.Field(aKey, aValue, PyLucene.Field.Store.NO, tokenize and PyLucene.Field.Index.TOKENIZED or PyLucene.Field.Index.UN_TOKENIZED))

    def addToIndexWith(self, anIndexWriter):
        anIndexWriter.addDocument(self._document)

    def validate(self):
        if self._fields == [IDFIELD]:
            raise DocumentException('Empty document')

    def asDict(self):
        dictionary = {}
        for field in self._document.getFields():
            key = field.name()
            if not key in dictionary:
                dictionary[key] = []
            if not field.stringValue()  in dictionary[key]:
                dictionary[key].append(field.stringValue())
        return dictionary

    def __repr__(self):
        return repr(self.asDict())