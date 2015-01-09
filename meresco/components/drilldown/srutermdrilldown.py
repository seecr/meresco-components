## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2011-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from meresco.core import Observable, decorateWith, decorate
from .drilldown import _DRILLDOWN_HEADER, _DRILLDOWN_XSD_2007, _DRILLDOWN_XSD_2013, DRILLDOWN_FOOTER
from xml.sax.saxutils import escape as xmlEscape, quoteattr
from traceback import print_exc
from simplejson import dumps

from meresco.components.sru.diagnostic import generalSystemError

from weightless.core import compose

FORMAT_OLD_XML = 'xml2007'
FORMAT_XML = 'xml'
FORMAT_JSON = 'json'

class SruTermDrilldown(Observable):

    def __init__(self, defaultFormat=FORMAT_OLD_XML):
        Observable.__init__(self)
        if defaultFormat not in [FORMAT_JSON, FORMAT_XML, FORMAT_OLD_XML]:
            raise ValueError("Format '%s' not supported." % defaultFormat)
        self._defaultFormat = defaultFormat

    def extraResponseData(self, drilldownData, sruArguments, **kwargs):
        if drilldownData is None:
            return
        outputFormat = sruArguments.get('x-drilldown-format', [self._defaultFormat])[0]
        drilldownHeader = _DRILLDOWN_HEADER % (_DRILLDOWN_XSD_2007 if outputFormat == FORMAT_OLD_XML else _DRILLDOWN_XSD_2013)
        try:
            yield decorate(drilldownHeader, self._termDrilldown(drilldownData, format=outputFormat), DRILLDOWN_FOOTER)
        except Exception as e:
            print_exc()
            yield drilldownHeader + "<dd:term-drilldown>"
            yield generalSystemError(xmlEscape(e.args[0]))
            yield "</dd:term-drilldown>" + DRILLDOWN_FOOTER
            return

    @decorateWith("<dd:term-drilldown>", "</dd:term-drilldown>")
    @compose
    def _termDrilldown(self, drilldownData, format):
        if format == FORMAT_XML:
            self._dd_item = self._dd_item_new
            for facet in drilldownData:
                yield self._dd_navigator(facet['fieldname'], facet['terms'])
        elif format == FORMAT_JSON:
            yield "<dd:json>%s</dd:json>" % xmlEscape(dumps(drilldownData, indent=4))
        elif format == FORMAT_OLD_XML:
            self._dd_item = self._dd_item_old
            for facet in drilldownData:
                yield self._dd_navigator(facet['fieldname'], facet['terms'])
        else:
            raise ValueError("Expected x-drilldown-format to be one of: %s" % str([FORMAT_XML, FORMAT_JSON]))

    def _dd_navigator(self, fieldname, terms):
        try:
            firstTerm = terms[0]
            yield '<dd:navigator name=%s>' % quoteattr(fieldname)
            yield self._dd_item(firstTerm)
            for term in terms[1:]:
                yield self._dd_item(term)
            yield '</dd:navigator>'
        except IndexError:
            yield '<dd:navigator name=%s/>' % quoteattr(fieldname)
            return
        except Exception as e:
            yield generalSystemError(xmlEscape(str(e)))
            return

    def _dd_item_new(self, term):
        yield '<dd:item count=%s value=%s' % (quoteattr(str(term['count'])), quoteattr(str(term['term'])))
        if 'pivot' in term:
            yield '>'
            yield self._dd_navigator(term['pivot']['fieldname'], term['pivot']['terms'])
            yield '</dd:item>'
        else:
            yield '/>'

    def _dd_item_old(self, term):
        yield '<dd:item count=%s>%s</dd:item>' % (quoteattr(str(term['count'])), xmlEscape(str(term['term'])))

    def echoedExtraRequestData(self, sruArguments, **kwargs):
        requestedTerms = [singleRequest for request in sruArguments.get('x-term-drilldown',[]) for singleRequest in request.split(',') if singleRequest.strip()]
        if requestedTerms:
            outputFormat = sruArguments.get('x-drilldown-format', [self._defaultFormat])[0]
            if outputFormat == FORMAT_OLD_XML:
                yield _DRILLDOWN_HEADER % _DRILLDOWN_XSD_2007
                yield "<dd:term-drilldown>%s</dd:term-drilldown>" % xmlEscape(','.join(requestedTerms))
                yield DRILLDOWN_FOOTER
                return

            yield _DRILLDOWN_HEADER % _DRILLDOWN_XSD_2013
            yield '<dd:request>'
            for term in requestedTerms:
                yield "<dd:x-term-drilldown>%s</dd:x-term-drilldown>" % xmlEscape(term)
            if 'x-drilldown-format' in sruArguments:
                yield "<dd:x-drilldown-format>%s</dd:x-drilldown-format>" % xmlEscape(outputFormat)
            yield '</dd:request>'
            yield DRILLDOWN_FOOTER

SRUTermDrilldown = SruTermDrilldown