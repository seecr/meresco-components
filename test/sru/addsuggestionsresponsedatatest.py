## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase
from meresco.components.sru.addsuggestionsresponsedata import AddSuggestionsResponseData
from testhelpers import Response
from weightless.core import compose

class AddSuggestionsResponseDataTest(SeecrTestCase):

    def testCreateExtraResponseDataWithSingleSuggestions(self):
        suggestions = AddSuggestionsResponseData()
        response = Response(total=0, hits=[])
        response.suggestions={'query': (0, 5, ['que', 'emery', 'queen', 'qu<een'])}
        responseData = ''.join(compose(suggestions.extraResponseData(response=response, suggestionsQuery="query")))
        self.assertEqualsWS("""<suggestions xmlns="http://meresco.org/namespace/suggestions">
    <suggestion>que</suggestion>
    <suggestion>emery</suggestion>
    <suggestion>queen</suggestion>
    <suggestion>qu&lt;een</suggestion>
</suggestions>
""", responseData)

    def testCreateExtraResponseDataWithMultipleSuggestions(self):
        suggestions = AddSuggestionsResponseData()
        response = Response(total=0, hits=[])
        response.suggestions={'query': (0, 5, ['que', 'emery', 'queen']), 'value': (10, 15, ['valu', 'ot']) }
        responseData = ''.join(compose(suggestions.extraResponseData(response=response, suggestionsQuery="query AND value")))
        self.assertEqualsWS("""<suggestions xmlns="http://meresco.org/namespace/suggestions">
    <suggestion>que AND valu</suggestion>
    <suggestion>emery AND ot</suggestion>
</suggestions>
""", responseData)

    def testDoNothingIfNoSuggestionsInResponse(self):
        suggestions = AddSuggestionsResponseData()
        response = Response(total=0, hits=[])
        responseData = list(compose(suggestions.extraResponseData(response=response, suggestionsQuery="query")))
        self.assertEquals([], responseData)

    def testHarriePoter(self):
        suggestions = AddSuggestionsResponseData()
        response = Response(total=0, hits=[])
        response.suggestions={'harrie': (0, 6, ['harry', 'marie']), 'poter': (11, 16, ['potter', 'peter']) }
        responseData = ''.join(compose(suggestions.extraResponseData(response=response, suggestionsQuery="harrie AND poter")))
        self.assertEqualsWS("""<suggestions xmlns="http://meresco.org/namespace/suggestions">
    <suggestion>harry AND potter</suggestion>
    <suggestion>marie AND peter</suggestion>
</suggestions>
""", responseData)


