## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
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

from meresco.core import Observable, decorateWith
from drilldown import DRILLDOWN_HEADER, DRILLDOWN_FOOTER, DEFAULT_MAXIMUM_TERMS
from xml.sax.saxutils import escape as xmlEscape, quoteattr

from meresco.components.sru.diagnostic import generalSystemError

class SRUTermDrilldown(Observable):
    def __init__(self, sortedByTermCount=False):
        Observable.__init__(self)
        self._sortedByTermCount = sortedByTermCount
                
    @decorateWith(DRILLDOWN_HEADER, DRILLDOWN_FOOTER)
    def extraResponseData(self, cqlAbstractSyntaxTree=None, x_term_drilldown=None, **kwargs):
        if x_term_drilldown == None or len(x_term_drilldown) != 1:
            return
        def splitTermAndMaximum(s):
            l = s.split(":")
            if len(l) == 1:
                return l[0], DEFAULT_MAXIMUM_TERMS, self._sortedByTermCount
            return l[0], int(l[1]), self._sortedByTermCount

        fieldsAndMaximums = x_term_drilldown[0].split(",")
        fieldMaxTuples = (splitTermAndMaximum(s) for s in fieldsAndMaximums)

        if fieldsAndMaximums == [""]:
            raise StopIteration

        drilldownResults = self.any.drilldown(
            self.any.docsetFromQuery(cqlAbstractSyntaxTree),
            fieldMaxTuples)

        yield self._termDrilldown(drilldownResults)

    @decorateWith("<dd:term-drilldown>", "</dd:term-drilldown>")
    def _termDrilldown(self, drilldownResults):
        try:
            for fieldname, termCounts in drilldownResults:
                yield self._dd_navigator(fieldname, termCounts)
        except Exception, e:
            yield generalSystemError(xmlEscape(e.message))
            return

    def _dd_navigator(self, fieldname, termCounts):
        try:
            firstTerm, firstCount = termCounts.next()
            yield '<dd:navigator name=%s>' % quoteattr(fieldname)
            yield '<dd:item count=%s>%s</dd:item>' % (quoteattr(str(firstCount)), xmlEscape(str(firstTerm)))
            for term, count in termCounts:
                yield '<dd:item count=%s>%s</dd:item>' % (quoteattr(str(count)), xmlEscape(str(term)))
            yield '</dd:navigator>'
        except Exception, e:
            yield generalSystemError(xmlEscape(e.message))
            return
        
    @decorateWith(DRILLDOWN_HEADER, DRILLDOWN_FOOTER)
    def echoedExtraRequestData(self, x_term_drilldown=None, **kwargs):
        if x_term_drilldown and len(x_term_drilldown) == 1:
            yield "<dd:term-drilldown>"
            yield xmlEscape(x_term_drilldown[0])
            yield "</dd:term-drilldown>"
