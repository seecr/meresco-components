## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.core import Observable, decorateWith
from drilldown import DRILLDOWN_HEADER, DRILLDOWN_FOOTER, DEFAULT_MAXIMUM_TERMS
from xml.sax.saxutils import escape as xmlEscape, quoteattr
from traceback import print_exc

from meresco.components.sru.diagnostic import generalSystemError

from weightless.core import compose

class SRUTermDrilldown(Observable):
                
    def extraResponseData(self, drilldownData, **kwargs):
        if drilldownData is None:
            return
        try:
            yield self._termDrilldown(drilldownData)
        except Exception, e:
            print_exc()
            yield DRILLDOWN_HEADER + "<dd:term-drilldown>"
            yield generalSystemError(xmlEscape(e.message))
            yield "</dd:term-drilldown>" + DRILLDOWN_FOOTER
            return

    @decorateWith(DRILLDOWN_HEADER + "<dd:term-drilldown>", "</dd:term-drilldown>" + DRILLDOWN_FOOTER)
    @compose
    def _termDrilldown(self, drilldownData):
        for facet in drilldownData:
            yield self._dd_navigator(facet['fieldname'], facet['terms'])

    def _dd_navigator(self, fieldname, terms):
        try:
            firstTerm = terms[0]
            yield '<dd:navigator name=%s>' % quoteattr(fieldname)
            yield '<dd:item count=%s>%s</dd:item>' % (quoteattr(str(firstTerm['count'])), xmlEscape(str(firstTerm['term'])))
            for term in terms[1:]:
                yield '<dd:item count=%s>%s</dd:item>' % (quoteattr(str(term['count'])), xmlEscape(str(term['term'])))
            yield '</dd:navigator>'
        except IndexError:
            yield '<dd:navigator name=%s/>' % quoteattr(fieldname)
            return
        except Exception, e:
            yield generalSystemError(xmlEscape(str(e)))
            return
        
    @decorateWith(DRILLDOWN_HEADER, DRILLDOWN_FOOTER)
    def echoedExtraRequestData(self, sruArguments, **kwargs):
        if 'x-term-drilldown' in sruArguments and len(sruArguments['x-term-drilldown']) == 1:
            yield "<dd:term-drilldown>"
            yield xmlEscape(sruArguments['x-term-drilldown'][0])
            yield "</dd:term-drilldown>"
