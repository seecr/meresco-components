## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from xml.sax.saxutils import quoteattr, escape

from cqlparser.cqlparser import parseString as parseCQL

from meresco.core.observable import Observable
from meresco.core.generatorutils import decorateWith

from weightless import compose

from drilldown import DRILLDOWN_HEADER, DRILLDOWN_FOOTER

class SRUFieldDrilldown(Observable):
    @decorateWith(DRILLDOWN_HEADER, DRILLDOWN_FOOTER)
    def extraResponseData(self, query=None, x_field_drilldown=None, x_field_drilldown_fields=None, **kwargs):
        if not x_field_drilldown or len(x_field_drilldown) != 1:
            return
        if not x_field_drilldown_fields or len(x_field_drilldown_fields) != 1:
            return
        
        term = x_field_drilldown[0]
        fields = x_field_drilldown_fields[0].split(',')

        drilldownResults = self.drilldown(query, term, fields)
        yield "<dd:field-drilldown>"
        for field, count in drilldownResults:
            yield '<dd:field name=%s>%s</dd:field>' % (quoteattr(escape(str(field))), escape(str(count)))
        yield "</dd:field-drilldown>"

    def drilldown(self, query, term, fields):
        for field in fields:
            cqlString = '(%s) AND %s=%s' % (query, field, term)
            total, recordIds = self.any.executeCQL(cqlAbstractSyntaxTree=parseCQL(cqlString))
            yield field, total

    @decorateWith(DRILLDOWN_HEADER, DRILLDOWN_FOOTER)
    def echoedExtraRequestData(self, x_field_drilldown=None, x_field_drilldown_fields=None, **kwargs):
        if x_field_drilldown and len(x_field_drilldown) == 1:
            yield "<dd:field-drilldown>"
            yield escape(x_field_drilldown[0])
            yield "</dd:field-drilldown>"
        if x_field_drilldown_fields and len(x_field_drilldown_fields) == 1:
            yield "<dd:field-drilldown-fields>"
            yield escape(x_field_drilldown_fields[0])
            yield "</dd:field-drilldown-fields>"
