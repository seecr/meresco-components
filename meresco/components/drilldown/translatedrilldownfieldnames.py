## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2012 Stichting Kennisnet http://www.kennisnet.nl
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

class TranslateDrilldownFieldnames(Observable):
    def __init__(self, translate):
        Observable.__init__(self)
        self.translate = translate

    def executeQuery(self, facets=None, *args, **kwargs):
        facets = facets or []
        reverseLookup = {}
        translatedFacets = []
        for facet in facets:
            translatedFacet = facet.copy()
            translatedFacet['field'] = self.translate(facet['field'])
            translatedFacets.append(translatedFacet)
            reverseLookup[translatedFacet['field']] = facet['field']
        if translatedFacets:
            kwargs['facets'] = translatedFacets
        response = yield self.any.executeQuery(*args, **kwargs)
        if hasattr(response, 'drilldownData'):
            response.drilldownData = [(reverseLookup[field], termCounts)
                for field, termCounts in response.drilldownData]
        raise StopIteration(response)

