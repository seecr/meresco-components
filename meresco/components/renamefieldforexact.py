## begin license ##
# 
# "Edurep" is a service for searching in educational repositories.
# "Edurep" is developed for Stichting Kennisnet (http://www.kennisnet.nl) by
# Seek You Too (http://www.cq2.nl). The project is based on the opensource
# project Meresco (http://www.meresco.com). 
# 
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
# 
# This file is part of "Edurep"
# 
# "Edurep" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Edurep" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Edurep"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

class RenameFieldForExact(object):
    def __init__(self, untokenizedFields, untokenizedPrefix):
        self._untokenizedFields = [f for f in untokenizedFields if not f.endswith('*')]
        self._untokenizedFieldPrefixes = [f[:-1] for f in untokenizedFields if f.endswith('*')]
        self._untokenizedPrefix = untokenizedPrefix

    def canModify(self, node):
        #SEARCH_CLAUSE(INDEX(...), RELATION(COMPARITOR('exact')), SEARCH_TERM(..))
        if len(node.children) == 3 and \
                node.children[1].children[0].children[0] == 'exact' and \
                self._hasUntokenizedRenaming(node.children[0].children[0].children[0]):
            return True
        return False

    def modify(self, node):
        term = node.children[0].children[0]
        term.children = (self._untokenizedPrefix + term.children[0],)
        return node

    def _hasUntokenizedRenaming(self, fieldname):
        untokenizedField = self._untokenizedPrefix + fieldname
        return untokenizedField in self._untokenizedFields or any(untokenizedField.startswith(prefix) for prefix in self._untokenizedFieldPrefixes)

    def filterAndModifier(self):
        return self.canModify, self.modify

