## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2012, 2014-2015, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2011-2012, 2014-2015, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from xml.sax.saxutils import quoteattr, escape

from cqlparser import cqlToExpression

from meresco.core.observable import Observable
from meresco.core.generatorutils import decorateWith

from .drilldown import DRILLDOWN_HEADER, DRILLDOWN_FOOTER

class SruFieldDrilldown(Observable):
    def extraResponseData(self, query=None, sruArguments=None, **kwargs):
        if not 'x-field-drilldown' in sruArguments or len(sruArguments['x-field-drilldown']) != 1:
            return
        if not 'x-field-drilldown-fields' in sruArguments or len(sruArguments['x-field-drilldown-fields']) != 1:
            return

        term = sruArguments['x-field-drilldown'][0]
        fields = sruArguments['x-field-drilldown-fields'][0].split(',')

        drilldownResults = yield self.drilldown(query, term, fields)
        yield _fieldDrilldown(drilldownResults)

    def drilldown(self, query, term, fields):
        drilldownResult = []
        for field in fields:
            cqlString = '(%s) AND %s=%s' % (query, field, term)
            response = yield self.any.executeQuery(query=cqlToExpression(cqlString))
            drilldownResult.append((field, response.total))
        return drilldownResult

    @decorateWith(DRILLDOWN_HEADER, DRILLDOWN_FOOTER)
    def echoedExtraRequestData(self, sruArguments, **kwargs):
        if 'x-field-drilldown' in sruArguments and len(sruArguments['x-field-drilldown']) == 1:
            yield "<dd:field-drilldown>"
            yield escape(sruArguments['x-field-drilldown'][0])
            yield "</dd:field-drilldown>"
        if 'x-field-drilldown-fields' in sruArguments and len(sruArguments['x-field-drilldown-fields']) == 1:
            yield "<dd:field-drilldown-fields>"
            yield escape(sruArguments['x-field-drilldown-fields'][0])
            yield "</dd:field-drilldown-fields>"

@decorateWith(DRILLDOWN_HEADER + "<dd:field-drilldown>", "</dd:field-drilldown>" + DRILLDOWN_FOOTER)
def _fieldDrilldown(drilldownResults):
    for field, count in drilldownResults:
        yield '<dd:field name=%s>%s</dd:field>' % (quoteattr(escape(str(field))), escape(str(count)))

SRUFieldDrilldown = SruFieldDrilldown
