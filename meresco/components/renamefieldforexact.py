## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2011-2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

class RenameFieldForExact(object):
    def __init__(self, untokenizedFields, untokenizedPrefix):
        self._untokenizedFields = [f for f in untokenizedFields if not f.endswith('*')]
        self._untokenizedFieldPrefixes = [f[:-1] for f in untokenizedFields if f.endswith('*')]
        self._untokenizedPrefix = untokenizedPrefix

    def canModify(self, expression):
        return expression.relation == 'exact' and self._hasUntokenizedRenaming(expression.index)

    def modify(self, expression):
        expression.index = self._untokenizedPrefix + expression.index

    def _hasUntokenizedRenaming(self, fieldname):
        untokenizedField = self._untokenizedPrefix + fieldname
        return untokenizedField in self._untokenizedFields or any(untokenizedField.startswith(prefix) for prefix in self._untokenizedFieldPrefixes)

    def filterAndModifier(self):
        return self.canModify, self.modify

