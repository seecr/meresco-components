## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Stichting Kennisnet https://www.kennisnet.nl
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

from meresco.components.converter import Converter
from simplejson import dumps
from .objects import JsonDict, JsonList

class JsonToString(Converter):
    def _convert(self, anObject):
        return dumps(anObject, sort_keys=True, indent=4)

class StringToJson(Converter):
    def _convert(self, anObject):
        return {'{': JsonDict, '[': JsonList}[anObject[0]].loads(anObject)

__all__ = ["JsonToString", "StringToJson"]
