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

class AddSuggestionsResponseData(object):

    def extraResponseData(self, response, suggestionsQuery, **kwargs):
        if not hasattr(response, 'suggestions'):
            return
        yield '<suggestions xmlns="http://meresco.org/namespace/suggestions">\n'

        allSuggestions = [suggestions for (start, stop, suggestions) in response.suggestions.values()]

        shortest = min([len(suggestions) for suggestions in allSuggestions])
        for i in range(shortest):
            indexShift = 0
            newSuggestionsQuery = suggestionsQuery
            for word, (start, stop, suggestions) in response.suggestions.items():
                replaceWord = suggestions[i]
                newSuggestionsQuery = newSuggestionsQuery[:start+indexShift] + replaceWord + newSuggestionsQuery[1+stop+indexShift:]
                indexShift += len(replaceWord) - len(word)
            yield "<suggestion>%s</suggestion>\n" % newSuggestionsQuery
        yield '</suggestions>\n'

