## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2011-2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
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

class SearchTermFilterAndModifier(object):
    def __init__(self, shouldModifyFieldValue, valueModifier=None, fieldnameModifier=None):
        self._shouldModifyFieldValue = shouldModifyFieldValue
        self._valueModifier = valueModifier
        self._fieldnameModifier = fieldnameModifier

    def canModify(self, expression):
        return expression.index is not None and self._shouldModifyFieldValue(expression.index, expression.relation, expression.term)

    def modify(self, expression):
        if self._valueModifier:
            expression.term = str(self._valueModifier(expression.term))
        if self._fieldnameModifier:
            expression.index = str(self._fieldnameModifier(expression.index))

    def filterAndModifier(self):
        return self.canModify, self.modify

