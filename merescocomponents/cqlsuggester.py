
from merescocore.framework import Observable
from cqltermvisitor import getAllTerms

class CqlSuggester(Observable) :
    def suggestForCql(self, cqlAST) :
        termlist = getAllTerms(cqlAST)
        for term in termlist:
            suggestions = self.any.suggestionsFor(term)
            return suggestions
           