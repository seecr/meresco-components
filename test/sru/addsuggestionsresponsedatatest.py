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

from seecr.test import SeecrTestCase
from meresco.components.sru.addsuggestionsresponsedata import AddSuggestionsResponseData
from meresco.components.facetindex import Response
from weightless.core import compose

class AddSuggestionsResponseDataTest(SeecrTestCase):

    def testCreateExtraResponseData(self):
        suggestions = AddSuggestionsResponseData()
        response = Response(total=0, hits=[])
        response.suggestions={'query': (0, 5, ['que', 'emery', 'queen'])}
        responseData = ''.join(compose(suggestions.extraResponseData(response=response)))
        self.assertEqualsWS("""<suggestions xmlns="http://meresco.org/namespace/suggestions">
    <word start="0" end="5" name="query">
        <suggestion>que</suggestion>
        <suggestion>emery</suggestion>
        <suggestion>queen</suggestion>
    </word>
</suggestions>
""", responseData)

    def testDoNothingIfNoSuggestionsInResponse(self):
        suggestions = AddSuggestionsResponseData()
        response = Response(total=0, hits=[])
        responseData = list(compose(suggestions.extraResponseData(response=response)))
        self.assertEquals([], responseData)
