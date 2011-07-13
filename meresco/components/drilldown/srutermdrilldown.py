from meresco.core import Observable, decorateWith
from drilldown import DRILLDOWN_HEADER, DRILLDOWN_FOOTER, DEFAULT_MAXIMUM_TERMS
from xml.sax.saxutils import escape as xmlEscape, quoteattr

from meresco.components.sru.diagnostic import generalSystemError

class SRUTermDrilldown(Observable):
    def __init__(self, sortedByTermCount=False):
        Observable.__init__(self)
        self._sortedByTermCount = sortedByTermCount
                
    def extraResponseData(self, cqlAbstractSyntaxTree, x_term_drilldown=None, **kwargs):
        if x_term_drilldown == None or len(x_term_drilldown) != 1:
            return
        def splitTermAndMaximum(s):
            l = s.split(":")
            if len(l) == 1:
                return l[0], DEFAULT_MAXIMUM_TERMS, self._sortedByTermCount
            return l[0], int(l[1]), self._sortedByTermCount

        fieldsAndMaximums = x_term_drilldown[0].split(",")
        fieldMaxTuples = (splitTermAndMaximum(s) for s in fieldsAndMaximums)

        try:
            drilldownResults = yield self.asyncany.drilldown(
                cqlAbstractSyntaxTree,
                fieldMaxTuples)
            yield self._termDrilldown(drilldownResults)
        except Exception, e:
            yield DRILLDOWN_HEADER + "<dd:term-drilldown>"
            yield generalSystemError(xmlEscape(e.message))
            yield "</dd:term-drilldown>" + DRILLDOWN_FOOTER
            return

    @decorateWith(DRILLDOWN_HEADER + "<dd:term-drilldown>", "</dd:term-drilldown>" + DRILLDOWN_FOOTER)
    def _termDrilldown(self, drilldownResults):
        for fieldname, termCounts in drilldownResults:
            yield self._dd_navigator(fieldname, termCounts)

    def _dd_navigator(self, fieldname, termCounts):
        try:
            firstTerm, firstCount = termCounts.next()
            yield '<dd:navigator name=%s>' % quoteattr(fieldname)
            yield '<dd:item count=%s>%s</dd:item>' % (quoteattr(str(firstCount)), xmlEscape(str(firstTerm)))
            for term, count in termCounts:
                yield '<dd:item count=%s>%s</dd:item>' % (quoteattr(str(count)), xmlEscape(str(term)))
            yield '</dd:navigator>'
        except StopIteration:
            yield '<dd:navigator name=%s/>' % quoteattr(fieldname)
            return
        except Exception, e:
            yield generalSystemError(xmlEscape(e.message))
            return
        
    @decorateWith(DRILLDOWN_HEADER, DRILLDOWN_FOOTER)
    def echoedExtraRequestData(self, x_term_drilldown=None, **kwargs):
        if x_term_drilldown and len(x_term_drilldown) == 1:
            yield "<dd:term-drilldown>"
            yield xmlEscape(x_term_drilldown[0])
            yield "</dd:term-drilldown>"
