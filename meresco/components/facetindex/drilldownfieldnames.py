## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
#    Copyright (C) 2011 Maastricht University http://www.um.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from meresco.core.observable import Observable
from drilldown import NoFacetIndexException

class DrilldownFieldnames(Observable):
    def __init__(self, lookup):
        Observable.__init__(self)
        self.lookup = lookup

    def drilldown(self, docNumbers, fieldsAndMaximums):
        reverseLookup = {}
        translatedFields = []
        for field, maximum, sort in fieldsAndMaximums:
            translated = self.lookup(field)
            translatedFields.append((translated, maximum, sort))
            reverseLookup[translated] = field
        try:
            drilldownResults = self.any.drilldown(docNumbers, translatedFields)
            return [(reverseLookup[field], termCounts)
                for field, termCounts in drilldownResults]
        except NoFacetIndexException, e:
            raise NoFacetIndexException(reverseLookup[e.field], e.fields)
           

    def hierarchicalDrilldown(self, docset, fieldsAndMaximums):
        reverseLookup = {}
        translatedFields = []
        for fields, maximum, sort in fieldsAndMaximums:
            newFields = []
            for field in fields:
                translated = self.lookup(field)
                reverseLookup[translated] = field
                newFields.append(translated)
            translatedFields.append((newFields, maximum, sort))
        drilldownResults = self.any.hierarchicalDrilldown(docset, translatedFields)

        def translateField(remainderGenerator):
            for field in remainderGenerator:
                yield dict(
                    fieldname=reverseLookup[field['fieldname']], 
                    terms=(dict(
                        term=item['term'], 
                        count=item['count'], 
                        remainder=translateField(item['remainder'])) for item in field['terms']))

        return translateField(drilldownResults)
        #return [dict(fieldname=reverseLookup[fields['fieldname']], terms=fields['terms']) for fields in drilldownResults]
