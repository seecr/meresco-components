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
# Copyright (C) 2010, 2015, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012, 2015-2016, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2016 SURFmarket https://surf.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from .handlerequestfilter import HandleRequestFilter

class PathFilter(HandleRequestFilter):

    def __init__(self, subPaths, excluding=None):
        HandleRequestFilter.__init__(self, self._filter)
        self.updatePaths(subPaths, excluding)

    def _filter(self, path, **kwargs):
        matchesSubPath = [subPath for subPath in self._subPaths if path.startswith(subPath)]
        matchesExcludedPath = [excludedPath for excludedPath in self._excluding if path.startswith(excludedPath)]
        if matchesSubPath and not matchesExcludedPath:
            return True
        return False

    def updatePaths(self, subPaths, excluding=None):
        self._subPaths = subPaths
        if type(subPaths) == str:
            self._subPaths = [subPaths]
        self._excluding = excluding or []
