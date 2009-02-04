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

from cq2utils.xmlutils import findNamespaces
from merescocore.framework import Transparant

class OaiAddRecord(Transparant):
    def add(self, id, name, record):
        sets=set()
        if record.localName == "header" and record.namespaceURI == "http://www.openarchives.org/OAI/2.0/" and getattr(record, 'setSpec', None):
            sets.update((str(s), str(s)) for s in record.setSpec)

        if 'amara.bindery.root_base' in str(type(record)):
            record = record.childNodes[0]
        ns2xsd = _findSchema(record)
        nsmap = findNamespaces(record)
        ns = nsmap[record.prefix]
        schema, namespace = (ns2xsd.get(ns,''), ns)
        schema, namespace = self._magicSchemaNamespace(record.prefix, name, schema, namespace)
        metadataFormats=[(name, schema, namespace)]

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

def _findSchema(record):
    if 'amara.bindery.root_base' in str(type(record)):
        record = record.childNodes[0]
    ns2xsd = {}
    if hasattr(record, 'schemaLocation'):
        nsXsdList = record.schemaLocation.split()
        for n in range(0, len(nsXsdList), 2):
            ns2xsd[nsXsdList[n]] = nsXsdList[n+1]
    return ns2xsd
