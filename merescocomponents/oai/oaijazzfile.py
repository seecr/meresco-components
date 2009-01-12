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

from __future__ import with_statement
from merescocore.framework import Observable
from os.path import isdir, join, isfile
from os import makedirs, listdir, rename
from storage.storage import escapeName, unescapeName
from time import time, strftime, localtime
from itertools import ifilter

class OaiJazzFile(Observable):
    def __init__(self, aDirectory):
        self._directory = aDirectory
        isdir(aDirectory) or makedirs(aDirectory)
        isdir(join(aDirectory, 'sets')) or makedirs(join(aDirectory,'sets'))
        isdir(join(aDirectory, 'prefixes')) or makedirs(join(aDirectory,'prefixes'))
        self._prefixes = {}
        self._sets = {}
        self._stamp2identifier = {}
        self._identifier2stamp = {}
        self._deleted = set()
        self._read()

    def addOaiRecord(self, identifier, sets=[], metadataFormats=[]):
        assert [prefix for prefix, schema, namespace in metadataFormats], 'No metadataFormat specified for record with identifier "%s"' % identifier
        self._delete(identifier)
        stamp = self._stamp()
        prefixes = (prefix for prefix, schema, namespace in metadataFormats)
        setSpecs = (setSpec for setSpec, setName in sets)
        self._add(stamp, identifier, setSpecs, prefixes)
        self._store()

    def delete(self, identifier):
        oldPrefixes, oldSets = self._delete(identifier)
        stamp = self._stamp()
        self._add(stamp, identifier, oldSets, oldPrefixes)
        self._deleted.add(stamp)
        self._store()

    def oaiSelect(self, sets=[], prefix='oai_dc', continueAt='0', oaiFrom=None, oaiUntil=None):
        stampIds = iter(self._prefixes.get(prefix, []))
        if sets:
            stampIdsSets = [self._sets.get(set,[]) for set in sets]
            def predicate(stamp):
                for stampIdsFromSet in stampIdsSets:
                    if stamp in stampIdsFromSet:
                        return True
                return False
            stampIds = ifilter(predicate, stampIds)
        return (self._stamp2identifier.get(stampId) for stampId in stampIds)

    def getDatestamp(self, identifier):
        stamp = self._identifier2stamp.get(identifier, None)
        if stamp == None:
            return None
        return strftime('%Y-%m-%dT%H:%M:%SZ', localtime(stamp/1000000.0))

    def isDeleted(self, identifier):
        stamp = self._identifier2stamp.get(identifier, None)
        return stamp != None and stamp in self._deleted
    
    def _add(self, stamp, identifier, setSpecs, prefixes):
        for setSpec in setSpecs:
            self._sets.setdefault(setSpec,[]).append(stamp)
        for prefix in prefixes:
            self._prefixes.setdefault(prefix,[]).append(stamp)
        self._stamp2identifier[stamp]=identifier
        self._identifier2stamp[identifier]=stamp

        
    def _delete(self, identifier):
        stamp = self._identifier2stamp.get(identifier, None)
        oldPrefixes = []
        oldSets = []
        if stamp != None:
            del self._identifier2stamp[identifier]
            del self._stamp2identifier[stamp]
            for prefix, prefixStamps in self._prefixes.items():
                if stamp in prefixStamps:
                    prefixStamps.remove(stamp)
                    oldPrefixes.append(prefix)
            for setSpec, setStamps in self._sets.items():
                if stamp in setStamps:
                    setStamps.remove(stamp)
                    oldSets.append(setSpec)
            if stamp in self._deleted:
                self._deleted.remove(stamp)
        return oldPrefixes, oldSets

    def _read(self):
        self._prefixes = {}
        for prefix in listdir(join(self._directory, 'prefixes')):
            with open(join(self._directory, 'prefixes',prefix)) as f:
                self._prefixes[unescapeName(prefix)] = [stamp.strip() for stamp in f if stamp]
        self._sets = {}
        for set in listdir(join(self._directory, 'sets')):
            with open(join(self._directory, 'sets',prefix)) as f:
                self._sets[unescapeName(set)] = [stamp.strip() for stamp in f if stamp]
        self._stamp2identifier = {}
        self._identifier2stamp = {}
        identifiersFile = join(self._directory, 'identifiers')
        if isfile(identifiersFile):
            with open(identifiersFile) as f:
                for stamp, identifier in (line.strip().split(' ',1) for line in f):
                    self._stamp2identifier[stamp] = identifier
                    self._identifier2stamp[identifier] = stamp

    def _store(self):
        for prefix, stamps in self._prefixes.items():
            with open(join(self._directory, 'prefixes', '__tmp__'), 'w') as f:
                for s in stamps:
                    f.write('%s\n' % s)
            rename(join(self._directory, 'prefixes', '__tmp__'), join(self._directory, 'prefixes', escapeName(prefix)))
        for set, stamps in self._sets.items():
            with open(join(self._directory, 'sets', '__tmp__'), 'w') as f:
                for s in stamps:
                    f.write('%s\n' % s)
            rename(join(self._directory, 'sets', '__tmp__'), join(self._directory, 'sets', escapeName(set)))
        with open(join(self._directory, '__tmp__identifiers'), 'w') as f:
            for stamp, identifier in self._stamp2identifier.items():
                f.write('%s %s\n' % (stamp, identifier))
        rename(join(self._directory, '__tmp__identifiers'), join(self._directory, 'identifiers'))

    def _stamp(self):
        """time in microseconds"""
        return int(time()*1000000.0)

    #def addOaiRecord(self, identifier, sets=[], metadataFormats=[]):
        #self.any.deletePart(identifier, 'tombstone')
        #setSpecs, prefixes, na, na = self._getPreviousRecord(identifier)
        #prefixes.update(prefix for prefix, schema, namespace in metadataFormats)
        #assert prefixes, 'No metadataFormat specified for record with identifier "%s"' % identifier
        #setSpecs.update(setSpec for setSpec, setName in sets)
        #setSpecs = self._flattenSetHierarchy(setSpecs)
        #self.__updateAllPrefixes2(metadataFormats)
        #self._updateAllSets(setSpecs)
        #self._updateOaiMeta(identifier, setSpecs, prefixes)



    #THE FOLLOWING CODE MUST GO AWAY, but is in use.
    #def add(self, id, name, record):
        ## This is the old way of adding data to OAI. Some self-learning stuff
        ## is still applied, this should be refactored to special components
        ## addOaiRecord will be the new way today.
        #sets=set()
        #if record.localName == "header" and record.namespaceURI == "http://www.openarchives.org/OAI/2.0/" and getattr(record, 'setSpec', None):
            #sets.update((str(s), str(s)) for s in record.setSpec)

        #if 'amara.bindery.root_base' in str(type(record)):
            #record = record.childNodes[0]
        #ns2xsd = self._findSchema(record)
        #nsmap = findNamespaces(record)
        #ns = nsmap[record.prefix]
        #schema, namespace = (ns2xsd.get(ns,''), ns)
        #metadataFormats=[(name, schema, namespace)]

        #self.addOaiRecord(identifier=id, sets=sets, metadataFormats=metadataFormats)

    #def delete(self, id):
        #self.any.store(id, 'tombstone', '<tombstone/>')
        #sets, prefixes, na, na = self._getPreviousRecord(id)
        #self._updateOaiMeta(id, sets, prefixes)

    #def oaiSelect(self, sets=[], prefix='oai_dc', continueAt='0', oaiFrom=None, oaiUntil=None, batchSize=10):
        #def addRange(root, field, lo, hi, inclusive):
            #range = ConstantScoreRangeQuery(field, lo, hi, inclusive, inclusive)
            #root.add(range, BooleanClause.Occur.MUST)

        #if self.any.docCount() == 0:
            #return 0, []

        ##It is necessery here to work with the elemental objects, because the query parser transforms everything into lowercase
        #query = BooleanQuery()
        #query.add(TermQuery(Term('oaimeta.prefixes.prefix', prefix)), BooleanClause.Occur.MUST)

        #if continueAt != '0':
            #addRange(query, 'oaimeta.unique', continueAt, None, False)
        #if oaiFrom or oaiUntil:
            #oaiFrom = oaiFrom or None
            #oaiUntil = oaiUntil and self._fixUntilDate(oaiUntil) or None
            #addRange(query, 'oaimeta.stamp', oaiFrom, oaiUntil, True)
        #if sets:
            #if len(sets) == 1:
                #query.add(TermQuery(Term('oaimeta.sets.setSpec', sets[0])), BooleanClause.Occur.MUST)

            #else:
                #setQuery = BooleanQuery()
                #for set in sets:
                    #setQuery.add(TermQuery(Term('oaimeta.sets.setSpec', set)), BooleanClause.Occur.SHOULD)
                #query.add(setQuery, BooleanClause.Occur.MUST)
        #total, recordIds = self.any.executeQuery(query, sortBy='oaimeta.unique', stop=batchSize)
        #return total, recordIds

    #def getAllPrefixes(self):
        #return set((prefix, xsd, ns) for prefix, (xsd, ns) in self._getAllPrefixes().items())

    #def getUnique(self, id):
        #sets, prefixes, stamp, unique = self._getPreviousRecord(id)
        #return unique

    #def getDatestamp(self, id):
        #sets, prefixes, stamp, unique = self._getPreviousRecord(id)
        #return stamp

    #def getSets(self, id):
        #sets, prefixes, stamp, unique = self._getPreviousRecord(id)
        #return list(sets)

    #def getParts(self, id):
        #sets, prefixes, stamp, unique = self._getPreviousRecord(id)
        #return list(prefixes)

    #def isDeleted(self, id):
        #ignored, hasTombStone = self.any.isAvailable(id, 'tombstone')
        #return hasTombStone

    #def oaiRecordExists(self, id):
        #hasRecord, hasMeta = self.any.isAvailable(id, 'oaimeta')
        #return hasRecord and hasMeta

    #def listSets(self):
        #return list(self._getAllSets())

################################################################################
    ## test only?
    #def listAll(self):
        #total, hits = self.any.executeQuery(MatchAllDocsQuery())
        #return hits

################################################################################

    #def _findSchema(self, record):
        #if 'amara.bindery.root_base' in str(type(record)):
            #record = record.childNodes[0]
        #ns2xsd = {}
        #if hasattr(record, 'schemaLocation'):
            #nsXsdList = record.schemaLocation.split()
            #for n in range(0, len(nsXsdList), 2):
                #ns2xsd[nsXsdList[n]] = nsXsdList[n+1]
        #return ns2xsd

    #def __updateAllPrefixes2(self, metadataFormats):
        #allPrefixes = self._getAllPrefixes()
        #for prefix, schema, namespace in metadataFormats:
            #if prefix not in allPrefixes:
               #allPrefixes[prefix] = (schema, namespace)
        #prefixesXml = '<ListMetadataFormats>%s</ListMetadataFormats>' % \
            #''.join(prefixTemplate % (prefix, xsd, ns) \
                #for prefix, (xsd, ns) in allPrefixes.items())
        #self.any.store('__all_prefixes__', '__prefixes__', prefixesXml)

    #def _updateAllPrefixes(self, prefix, record):
        #if 'amara.bindery.root_base' in str(type(record)):
            #record = record.childNodes[0]
        #allPrefixes = self._getAllPrefixes()
        #ns2xsd = self._findSchema(record)
        #nsmap = findNamespaces(record)
        #ns = nsmap[record.prefix]
        #newPrefixInfo = (ns2xsd.get(ns,''), ns)
        #if prefix not in allPrefixes:
            #allPrefixes[prefix] = newPrefixInfo
        #prefixesXml = '<ListMetadataFormats>' + ''.join(prefixTemplate % (prefix, xsd, ns) for prefix, (xsd, ns) in allPrefixes.items()) + '</ListMetadataFormats>'
        #self.any.store('__all_prefixes__', '__prefixes__', prefixesXml)

    #def _fixUntilDate(self, aString):
        #dateRE = compile('^\d{4}-\d{2}-\d{2}$')
        #result = aString
        #if dateRE.match(aString):
            #dateFromString = strptime(aString, '%Y-%m-%d')
            #datePlusOneDay = localtime(mktime(dateFromString) + 24*3600)
            #result = strftime('%Y-%m-%dT%H:%M:%SZ', datePlusOneDay)
        #return result

    #def _flattenSetHierarchy(self, sets):
        #""""[1:2:3, 1:2:4] => [1, 1:2, 1:2:3, 1:2:4]"""
        #result = set()
        #for setSpec in sets:
            #parts = setSpec.split(':')
            #for i in range(1, len(parts) + 1):
                #result.add(':'.join(parts[:i]))
        #return result

    #def _getAllSets(self):
        #allSets = set()
        #if (True, True) == self.any.isAvailable('__all_sets__', '__sets__'):
            #setsXml = parse(self.any.getStream('__all_sets__', '__sets__'))
            #allSets.update(setsXml.xpath('/sets:__sets__/sets:setSpec/text()', {'sets':'http://meresco.com/namespace/meresco/oai/sets'}))
        #return allSets

    #def _updateAllSets(self, sets):
        #allSets = self._getAllSets()
        #allSets.update(sets)
        #spec= '<setSpec>%s</setSpec>'
        #setsXml = '<__sets__ xmlns="http://meresco.com/namespace/meresco/oai/sets">' + ''.join(spec % set for set in allSets) + '</__sets__>'
        #self.any.store('__all_sets__', '__sets__', setsXml)

    #def _getAllPrefixes(self):
        #allPrefixes = {}
        #if (True, True) == self.any.isAvailable('__all_prefixes__', '__prefixes__'):
            #allPrefixesXml = bind_stream(self.any.getStream('__all_prefixes__', '__prefixes__')).ListMetadataFormats
            #for info in allPrefixesXml.metadataFormat:
                #allPrefixes[str(info.metadataPrefix)] = (str(info.schema), str(info.metadataNamespace))
        #return allPrefixes

    #def _gettime(self):
        #return gmtime()

    #def _updateOaiMeta(self, id, sets, prefixes):
        #unique = self._numberGenerator.next()
        #stamp =  strftime('%Y-%m-%dT%H:%M:%SZ', self._gettime())
        #newOaiMeta = createOaiMeta(sets, prefixes, stamp, unique)
        #metaRecord = ''.join(newOaiMeta)
        #self.do.add(id, 'oaimeta', str(metaRecord))

    #def _getPreviousRecord(self, id):
        #sets = set()
        #prefixes = set()
        #stamp = unique = None
        #if (True, True) == self.any.isAvailable(id, 'oaimeta'):
            #data = ''.join(self.any.getStream(id, 'oaimeta'))
            #sets, prefixes, stamp, unique = parseOaiMeta(data)
        #return sets, prefixes, stamp, unique