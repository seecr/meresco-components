
from merescocore.framework import Observable
from oaijazz import RecordId, WrapIterable

class OaiIdentifierRename(Observable):
    def __init__(self, repositoryIdentifier):
        Observable.__init__(self)
        self._repositoryIdentifier = repositoryIdentifier
        self._prefix = 'oai:%s:' % self._repositoryIdentifier

    def _strip(self, identifier):
        return identifier[len(self._prefix):]

    def _append(self, identifier):
        if hasattr(identifier, 'stamp'):
            return RecordId(self._prefix + identifier, identifier.stamp)
        return self._prefix + identifier


    def isDeleted(self, identifier):
        return self.any.isDeleted(self._strip(identifier))

    def getUnique(self, identifier):
        return self.any.getUnique(self._strip(identifier))

    def getDatestamp(self, identifier):
        return self.any.getDatestamp(self._strip(identifier))
    
    def isAvailable(self, id, partName):
        return self.any.isAvailable(self._strip(id), partName)
    
    def getPrefixes(self, identifier):
        return self.any.getPrefixes(self._strip(identifier))
    
    def getSets(self, identifier):
        return self.any.getSets(self._strip(identifier))

    def write(self, sink, id, partName):
        return self.any.write(sink, self._strip(id), partName)
    
    def unknown(self, message, *args, **kwargs):
        return self.all.unknown(message, *args, **kwargs)

    def oaiSelect(self, *args, **kwargs):
        return WrapIterable((self._append(recordId) for recordId in self.any.oaiSelect(*args, **kwargs)))
            