# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012, 2015, 2017 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2017 SURFmarket https://surf.nl
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

from .converter import Converter
from cqlparser.cqltoexpression import QueryExpression

class CqlMultiSearchClauseConversion(Converter):
    def __init__(self, filtersAndModifiers, fromKwarg, toKwarg=None, name=None):
        Converter.__init__(self, name=name, fromKwarg=fromKwarg, toKwarg=toKwarg)
        self._filtersAndModifiers = filtersAndModifiers

    def _convert(self, query):
        if not isinstance(query, QueryExpression):
            return query
        for expression in query.iter():
            for searchClauseFilter, searchClauseModifier in self._filtersAndModifiers:
                if expression.isSearchterm() and searchClauseFilter(expression):
                    searchClauseModifier(expression)
        return query

class CqlSearchClauseConversion(CqlMultiSearchClauseConversion):
    def __init__(self, searchClauseFilter, modifier, fromKwarg, toKwarg=None, name=None):
        CqlMultiSearchClauseConversion.__init__(self, filtersAndModifiers=[(searchClauseFilter, modifier)], name=name, fromKwarg=fromKwarg, toKwarg=toKwarg)

