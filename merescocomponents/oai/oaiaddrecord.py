
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

def _findSchema(record):
    if 'amara.bindery.root_base' in str(type(record)):
        record = record.childNodes[0]
    ns2xsd = {}
    if hasattr(record, 'schemaLocation'):
        nsXsdList = record.schemaLocation.split()
        for n in range(0, len(nsXsdList), 2):
            ns2xsd[nsXsdList[n]] = nsXsdList[n+1]
    return ns2xsd
