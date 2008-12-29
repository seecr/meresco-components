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

class AddCommand(object):

    def __init__(self, index, document):
        self.index = index
        self.document = document

    def __call__(self):
        self.index.addDocument(self.document)

    def __eq__(self, other):
        return other == self.document.identifier

class DeleteCommand(object):

    def __init__(self, index, anId):
        self.index = index
        self.anId = anId

    def __call__(self):
        self.index.delete(self.anId)


class IndexFacade(object):
    def __init__(self, index):
        self._queue = []
        self.index = index

    def addDocument(self, document):
        self._queue.append(AddCommand(self.index, document))

    def delete(self, anId):
        if anId in self._queue:
            self._queue.remove(anId)
        else:
            self._queue.append(DeleteCommand(self.index, anId))

    def executeQuery(self, query):
        return self.index.executeQuery(query)

    def flush(self):
        for command in self._queue:
            command()
        self.index._reopenIndex()
        self._queue = []
