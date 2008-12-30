## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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

from StringIO import StringIO
from lxml.etree import parse

from meresco.framework import Observable
from meresco.components import XmlCompose


PROVENANCE_TEMPLATE = """<provenance xmlns="http://www.openarchives.org/OAI/2.0/provenance"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/provenance
                      http://www.openarchives.org/OAI/2.0/provenance.xsd">

<originDescription harvestDate="%(harvestDate)s" altered="true">
  <baseURL>%(baseURL)s</baseURL>
  <identifier>%(identifier)s</identifier>
  <datestamp>%(datestamp)s</datestamp>
  <metadataNamespace>%(metadataNamespace)s</metadataNamespace>
</originDescription>
</provenance>
"""

class OaiProvenance(XmlCompose):
    def __init__(self, nsMap, baseURL, harvestDate, metadataNamespace, identifier, datestamp):
        XmlCompose.__init__(self,
            PROVENANCE_TEMPLATE,
            nsMap,
            baseURL=baseURL,
            harvestDate=harvestDate,
            metadataNamespace=metadataNamespace,
            identifier=identifier,
            datestamp=datestamp)

    def provenance(self, aRecordId):
        return self.getRecord(aRecordId)
        
