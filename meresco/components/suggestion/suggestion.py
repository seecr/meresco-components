## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012-2013, 2015, 2018 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2013 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from meresco.core import Observable


class Suggestion(Observable):
    def __init__(self, count, field, allowOverrideField=False, maximumCount=None, suggestMode=None):
        Observable.__init__(self)
        self._count = count
        self._field = field
        self._suggestMode = suggestMode
        self._allowOverrideField = allowOverrideField
        self._maximumCount = maximumCount

    def executeQuery(self, **kwargs):
        suggestionRequest = None
        extraArguments = kwargs.get('extraArguments')
        if not extraArguments is None:
            xSuggestionsQuery = extraArguments.get('x-suggestionsQuery', [None])[0]
            if xSuggestionsQuery:
                suggestionRequest = dict(
                    count=self._getCount(extraArguments),
                    field=self._getField(extraArguments),
                    suggests=xSuggestionsQuery.split())
                suggestMode = self._getSuggestMode(extraArguments)
                if suggestMode:
                    suggestionRequest['mode'] = suggestMode
        response = yield self.any.executeQuery(suggestionRequest=suggestionRequest, **kwargs)
        return response

    def extraResponseData(self, response, sruArguments, **kwargs):
        if not hasattr(response, 'suggestions'):
            return
        sortedSuggestions = sorted(response.suggestions.items())
        if not sortedSuggestions:
            return

        yield '<suggestions xmlns="http://meresco.org/namespace/suggestions">\n'
        shortest = min([len(suggestions) for word, suggestions in sortedSuggestions])
        for i in range(shortest):
            suggestionWords = str(sruArguments['x-suggestionsQuery'][0]).split()
            for word, suggestions in reversed(sortedSuggestions):
                replaceWord = suggestions[i]
                suggestionWords[suggestionWords.index(word)] = replaceWord
            yield "<suggestion>%s</suggestion>\n" % xmlEscape(' '.join(suggestionWords))
        yield '</suggestions>\n'

    def echoedExtraRequestData(self, sruArguments, **kwargs):
        if 'x-suggestionsQuery' not in sruArguments:
            return
        yield '<suggestions xmlns="http://meresco.org/namespace/suggestions">\n'
        yield '<query>%s</query>' % xmlEscape(sruArguments['x-suggestionsQuery'][0])
        yield '<count>%s</count>' % self._getCount(sruArguments)
        yield '<field>%s</field>' % xmlEscape(self._getField(sruArguments))
        suggestMode = self._getSuggestMode(sruArguments)
        if suggestMode:
            yield '<mode>%s</mode>' % xmlEscape(suggestMode)
        yield '</suggestions>'

    def _getField(self, arguments):
        if not self._allowOverrideField:
            return self._field
        return arguments.get('x-suggestionsField', [self._field])[0]

    def _getCount(self, arguments):
        count = max(1, int(arguments.get('x-suggestionsCount', [self._count])[0]))
        if self._maximumCount:
            count = min(count, self._maximumCount)
        return count

    def _getSuggestMode(self, arguments):
        return arguments.get('x-suggestMode', [self._suggestMode])[0]
