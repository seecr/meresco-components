# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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
from xml.sax.saxutils import escape as xmlEscape

from oaiverb import OaiVerb
from meresco.core.generatorutils import decorate

class OaiRecordVerb(OaiVerb):

    def writeRecord(self, webRequest, recordId, writeBody=True):
        isDeletedStr = self.any.isDeleted(recordId) and ' status="deleted"' or ''
        datestamp = self.any.getDatestamp(recordId)
        setSpecs = self._getSetSpecs(recordId)
        if writeBody:
            webRequest.write('<record>')

        webRequest.write("""<header%s>
            <identifier>%s</identifier>
            <datestamp>%s</datestamp>
            %s
        </header>""" % (isDeletedStr, xmlEscape(recordId.encode('utf-8')), datestamp, setSpecs))

        if writeBody and not isDeletedStr:
            webRequest.write('<metadata>')
            self.any.write(webRequest, recordId, self._metadataPrefix)
            webRequest.write('</metadata>')

        provenance = self.all.provenance(recordId)
        for line in decorate('<about>', provenance, '</about>'):
            webRequest.write(line)

        if writeBody:
            webRequest.write('</record>')

    def _getSetSpecs(self, recordId):
        sets = self.any.getSets(recordId)
        if sets:
            return ''.join('<setSpec>%s</setSpec>' % xmlEscape(setSpec) for setSpec in sets)
        return ''
