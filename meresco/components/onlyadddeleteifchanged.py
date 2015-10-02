## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
#
# This file is part of "Meresco Components"
#
# "Meresco Components" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Components" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Components"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from meresco.core import Observable


class OnlyAddDeleteIfChanged(Observable):
    def add(self, identifier, partname, data):
        storedData = None
        record = self.call.getRecord(identifier=identifier)
        if not record is None:
            try:
                storedData = self.call.getData(identifier=identifier, name=partname)
            except KeyError:
                pass
        if data != storedData:
            yield self.all.add(identifier=identifier, partname=partname, data=data)

    def delete(self, identifier):
        record = self.call.getRecord(identifier=identifier)
        if record is None or not record.isDeleted:
            yield self.all.delete(identifier=identifier)
