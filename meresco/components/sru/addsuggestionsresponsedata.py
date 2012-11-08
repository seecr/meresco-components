## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from xml.sax.saxutils import escape as xmlEscape

class AddSuggestionsResponseData(object):

    def extraResponseData(self, response, suggestionsQuery, **kwargs):
        if not hasattr(response, 'suggestions'):
            return

        sortedSuggestions = sorted(response.suggestions.items(), key=lambda (word, (start, stop, suggestions)): start)
        allSuggestions = [suggestions for (word, (start, stop, suggestions)) in sortedSuggestions]

        if not allSuggestions:
            return

        yield '<suggestions xmlns="http://meresco.org/namespace/suggestions">\n'
        shortest = min([len(suggestions) for suggestions in allSuggestions])
        for i in range(shortest):
            newSuggestionsQuery = suggestionsQuery
            for word, (start, stop, suggestions) in reversed(sortedSuggestions):
                replaceWord = suggestions[i]
                leftPart = newSuggestionsQuery[:start]
                rightPart = newSuggestionsQuery[stop:]

                newSuggestionsQuery = leftPart + replaceWord + rightPart
            yield "<suggestion>%s</suggestion>\n" % xmlEscape(newSuggestionsQuery)
        yield '</suggestions>\n'

