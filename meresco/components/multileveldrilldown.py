## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2008-2009, 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2008-2009 Technische Universiteit Delft http://www.tudelft.nl
# Copyright (C) 2008-2009 Universiteit van Tilburg http://www.uvt.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

class MultiLevelDrilldownException(Exception):
    pass

class MultiLevelDrilldown(Observable):
    def __init__(self, multiLevelFieldsDict):
        Observable.__init__(self)
        self._multiLevelFields = multiLevelFieldsDict
        for key, multilevelFields in multiLevelFieldsDict.items():
            for multilevelField in multilevelFields:
                assert len(multilevelField) == 3, 'multilevelFields for %s should be a list of tuples with: levelField, maximumCount, sorted' % key

    def multiLevelDrilldown(self, docset, drilldownFields):
        for field in drilldownFields:
            if field not in self._multiLevelFields:
                raise MultiLevelDrilldownException("No drilldown fields defined for '%s'." % field)
            resultFieldName, resultTermCounts = None, []
            for levelField, maximumCount, sorted in self._multiLevelFields[field]:
                drilldownResult = yield self.any.drilldown(docset, [(levelField, maximumCount, sorted)])
                fieldName, termCounts = next(drilldownResult)
                termCounts = list(termCounts)
                if len(termCounts) > 0:
                    resultFieldName, resultTermCounts = fieldName, termCounts
                if len(termCounts) < maximumCount:
                    break

            yield (field, resultFieldName), resultTermCounts
