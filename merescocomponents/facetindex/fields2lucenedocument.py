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
from document import Document

class Fields2LuceneDocumentTx(object):

    def __init__(self, resourceManager, untokenized):
        self.resourceManager = resourceManager
        self.fields = {}
        self._untokenized = untokenized

    def addField(self, name, value):
        if not name in self.fields:
            self.fields[name] = []
        self.fields[name].append(value)

    def commit(self):
        if not self.fields.keys():
            return
        document = Document(self.resourceManager.tx.locals['id'])
        for name, values in self.fields.items():
            for value in values:
                document.addIndexedField(name, value, not name in self._untokenized)
        self.resourceManager.do.addDocument(document)

    def rollback(self):
        pass

