#copyright

from merescocore.framework import Observable


class CqlSuggester(Observable) :
    def suggestForCql(self, cqlAST) :
        index = 0
        currentTerm = cqlAST.children()[index].children()[0].children()[0].children()[0].children()[0]
        return self.any.suggestionsFor(currentTerm)