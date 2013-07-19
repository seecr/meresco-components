## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2013 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
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

from seecr.test import SeecrTestCase, CallTrace
from seecr.utils.generatorutils import returnValueFromGenerator
from meresco.components.suggestion import Suggestion
from testhelpers import Response
from weightless.core import compose

class SuggestionTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.observer = CallTrace('observer')
        self.response = Response(total=0, hits=[])
        def executeQuery(**kwargs):
            raise StopIteration(self.response)
            yield
        self.observer.methods['executeQuery'] = executeQuery

    def testCreateExtraResponseDataWithSingleSuggestions(self):
        suggestions = Suggestion(count=1, field='afield')
        response = Response(total=0, hits=[])
        response.suggestions={'query': (0, 5, ['que', 'emery', 'queen', 'qu<een'])}
        responseData = ''.join(compose(suggestions.extraResponseData(response=response, sruArguments={'x-suggestionsQuery':["query"]})))
        self.assertEqualsWS("""<suggestions xmlns="http://meresco.org/namespace/suggestions">
    <suggestion>que</suggestion>
    <suggestion>emery</suggestion>
    <suggestion>queen</suggestion>
    <suggestion>qu&lt;een</suggestion>
</suggestions>
""", responseData)

    def testCreateExtraResponseDataWithMultipleSuggestions(self):
        suggestions = Suggestion(count=1, field='afield')
        response = Response(total=0, hits=[])
        response.suggestions={'query': (0, 5, ['que', 'emery', 'queen']), 'value': (10, 15, ['valu', 'ot']) }
        responseData = ''.join(compose(suggestions.extraResponseData(response=response, sruArguments={'x-suggestionsQuery':["query AND value"]})))
        self.assertEqualsWS("""<suggestions xmlns="http://meresco.org/namespace/suggestions">
    <suggestion>que AND valu</suggestion>
    <suggestion>emery AND ot</suggestion>
</suggestions>
""", responseData)

    def testDoNothingIfNoSuggestionsInResponse(self):
        suggestions = Suggestion(count=1, field='afield')
        response = Response(total=0, hits=[])
        responseData = list(compose(suggestions.extraResponseData(response=response, sruArguments={'x-suggestionsQuery': ["query"]})))
        self.assertEquals([], responseData)

    def testHarriePoter(self):
        suggestions = Suggestion(count=1, field='afield')
        response = Response(total=0, hits=[])
        response.suggestions={'harrie': (0, 6, ['harry', 'marie']), 'poter': (11, 16, ['potter', 'peter']) }
        responseData = ''.join(compose(suggestions.extraResponseData(response=response, sruArguments={'x-suggestionsQuery':["harrie AND poter"]})))
        self.assertEqualsWS("""<suggestions xmlns="http://meresco.org/namespace/suggestions">
    <suggestion>harry AND potter</suggestion>
    <suggestion>marie AND peter</suggestion>
</suggestions>
""", responseData)

    def testEchoedExtraRequestData(self):
        suggestion = Suggestion(count=1, field='afi>eld')

        result = "".join(list(suggestion.echoedExtraRequestData(sruArguments={'x-suggestionsQuery': ['que<ry']})))

        self.assertEqualsWS("""
            <suggestions xmlns="http://meresco.org/namespace/suggestions">
                <query>que&lt;ry</query>
                <count>1</count>
                <field>afi&gt;eld</field>
            </suggestions>""", result)

    def testEchoedExtraRequestDataOtherCountField(self):
        suggestion = Suggestion(count=1, field='afield', allowOverrideField=True)

        result = "".join(list(suggestion.echoedExtraRequestData(sruArguments={'x-suggestionsQuery': ['query'], 'x-suggestionsCount': ['2'], 'x-suggestionsField': ['field']})))

        self.assertEqualsWS("""
            <suggestions xmlns="http://meresco.org/namespace/suggestions">
                <query>query</query>
                <count>2</count>
                <field>field</field>
            </suggestions>""", result)

    def testXSuggestionQueryToSuggestionRequest(self):
        extraArguments = {'x-suggestionsQuery': ['query']}
        suggestion = Suggestion(count=10, field='dcterms:title')
        suggestion.addObserver(self.observer)
        result = returnValueFromGenerator(suggestion.executeQuery(kwarg='value', extraArguments=extraArguments))
        self.assertTrue(result == self.response)
        self.assertEquals(['executeQuery'], self.observer.calledMethodNames())
        methodKwargs = self.observer.calledMethods[0].kwargs
        self.assertEquals(dict(count=10, field='dcterms:title', query='query'), methodKwargs['suggestionRequest'])

    def testXSuggestionQueryCountAndFieldToSuggestionRequest(self):
        extraArguments = {'x-suggestionsQuery': ['query'], 'x-suggestionsField': ['fieldname'], 'x-suggestionsCount': ['5']}
        suggestion = Suggestion(count=10, field='dcterms:title', allowOverrideField=True)
        suggestion.addObserver(self.observer)
        result = returnValueFromGenerator(suggestion.executeQuery(kwarg='value', extraArguments=extraArguments))
        self.assertTrue(result == self.response)
        self.assertEquals(['executeQuery'], self.observer.calledMethodNames())
        methodKwargs = self.observer.calledMethods[0].kwargs
        self.assertEquals(dict(count=5, field='fieldname', query='query'), methodKwargs['suggestionRequest'])

    def testXSuggestionCountMaximized(self):
        extraArguments = {'x-suggestionsQuery': ['query'], 'x-suggestionsCount': ['50']}
        suggestion = Suggestion(count=10, field='dcterms:title', maximumCount=20)
        suggestion.addObserver(self.observer)
        result = returnValueFromGenerator(suggestion.executeQuery(kwarg='value', extraArguments=extraArguments))
        self.assertTrue(result == self.response)
        self.assertEquals(['executeQuery'], self.observer.calledMethodNames())
        methodKwargs = self.observer.calledMethods[0].kwargs
        self.assertEquals(dict(count=20, field='dcterms:title', query='query'), methodKwargs['suggestionRequest'])

    def testXSuggestionFieldDisabled(self):
        extraArguments = {'x-suggestionsQuery': ['query'], 'x-suggestionsField': ['fieldname'], 'x-suggestionsCount': ['5']}
        suggestion = Suggestion(count=10, field='dcterms:title', allowOverrideField=False)
        suggestion.addObserver(self.observer)
        result = returnValueFromGenerator(suggestion.executeQuery(kwarg='value', extraArguments=extraArguments))
        self.assertTrue(result == self.response)
        self.assertEquals(['executeQuery'], self.observer.calledMethodNames())
        methodKwargs = self.observer.calledMethods[0].kwargs
        self.assertEquals(dict(count=5, field='dcterms:title', query='query'), methodKwargs['suggestionRequest'])

    def testNoSuggestionQuery(self):
        extraArguments = {'x-suggestionsQuery': [''], 'x-suggestionsField': ['fieldname'], 'x-suggestionsCount': ['5']}
        suggestion = Suggestion(count=10, field='dcterms:title', allowOverrideField=False)
        suggestion.addObserver(self.observer)
        result = returnValueFromGenerator(suggestion.executeQuery(kwarg='value', extraArguments=extraArguments))
        self.assertEquals(['executeQuery'], self.observer.calledMethodNames())
        methodKwargs = self.observer.calledMethods[0].kwargs
        self.assertEquals(None, methodKwargs['suggestionRequest'])

