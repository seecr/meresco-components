## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2011-2012, 2015-2016, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2011, 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from meresco.core import Transparent
from xml.sax.saxutils import escape as xmlEscape

class CombineParts(Transparent):
    def __init__(self, combinations, allowMissingParts=None):
        Transparent.__init__(self)
        self._combinations = combinations
        self._allowMissingParts = allowMissingParts or []

    def retrieveData(self, identifier, name):
        return self.getData(identifier=identifier, name=name)
        yield

    def getData(self, identifier, name):
        if not name in self._combinations.keys():
            return self.call.getData(identifier=identifier, name=name)

        resultparts = []
        for subpart in self._combinations[name]:
            try:
                resultparts.append((subpart, self.call.getData(identifier=identifier, name=subpart)))
            except (IOError, KeyError):
                if subpart not in self._allowMissingParts:
                    raise
        def result():
            yield b'<doc:document xmlns:doc="http://meresco.org/namespace/harvester/document">'
            for subpart, data in resultparts:
                yield b'<doc:part name="%b">' % bytes(xmlEscape(subpart), encoding='utf-8')
                yield data
                yield b'</doc:part>'
            yield b'</doc:document>'
        return b''.join(result())
