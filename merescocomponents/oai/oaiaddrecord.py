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

from merescocore.framework import Transparant
from lxml.etree import iselement

namespaces = {
    'oai': 'http://www.openarchives.org/OAI/2.0/',
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
}

class OaiAddRecord(Transparant):
    def add(self, id, partName, record):
        record = record if iselement(record) else record.getroot()
        setSpecs = record.xpath('/oai:header/oai:setSpec/text()', namespaces=namespaces)
        sets = set((str(s), str(s)) for s in setSpecs)
        
        namespace = record.nsmap.get(record.prefix or None, '') 
        schemaLocations = record.xpath('@xsi:schemaLocation', namespaces=namespaces)
        ns2xsd = ''.join(schemaLocations).split()
        schema = dict(zip(ns2xsd[::2],ns2xsd[1::2])).get(namespace, '')
        schema, namespace = self._magicSchemaNamespace(record.prefix, partName, schema, namespace)
        metadataFormats=[(partName, schema, namespace)]

        self.do.addOaiRecord(identifier=id, sets=sets, metadataFormats=metadataFormats)

    def _magicSchemaNamespace(self, prefix, name, schema, namespace):
        searchForPrefix = prefix or name
        for oldprefix, oldschema, oldnamespace in self.any.getAllMetadataFormats():
            if searchForPrefix == oldprefix:
                return schema or oldschema, namespace or oldnamespace
        return schema, namespace

class OaiAddRecordWithDefaults(Transparant):
    def __init__(self, metadataFormats=[], sets=[]):
        Transparant.__init__(self)
        self._metadataFormats = metadataFormats
        self._sets = sets
        
    def add(self, id, name, record):
        self.do.addOaiRecord(identifier=id, sets=self._sets, metadataFormats=self._metadataFormats)

