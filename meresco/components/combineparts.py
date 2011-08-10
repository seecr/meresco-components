## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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
from xml.sax.saxutils import escape as xmlEscape

class CombineParts(Observable):
    def __init__(self, combinations):
        Observable.__init__(self)
        self._combinations = combinations

    def yieldRecord(self, identifier, partname):
        if not partname in self._combinations.keys():
            yield self.all.yieldRecord(identifier=identifier, partname=partname)
            return

        substuff = []
        for subpart in self._combinations[partname]:
            subgenerator = self.all.yieldRecord(identifier=identifier, partname=subpart)
            substuff.append((subpart, subgenerator.next(), subgenerator))

        yield '<doc:document xmlns:doc="http://meresco.org/namespace/harvester/document">' 
        for subpart, firstResult, remaining in substuff:
            yield '<doc:part name="%s">' % xmlEscape(subpart)
            yield firstResult
            yield remaining
            yield '</doc:part>'
        yield '</doc:document>'

