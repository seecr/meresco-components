## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010, 2012, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012-2013, 2016, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from lxml.etree import _Element, ElementTree, XML

from meresco.core import Observable

from meresco.components.xmlxpath import lxmlElementUntail
from meresco.components import lxmltobytes
from meresco.components.http.utils import ensureBytes
from warnings import warn
from meresco.xml.namespaces import namespaces as _namespaces


class Venturi(Observable):
    def __init__(self, should=None, could=None, namespaces=None, namespaceMap=None):
        Observable.__init__(self)
        if namespaceMap:
            warn("Please use 'namespaces=...'", DeprecationWarning)
            namespaces=namespaceMap
        self.xpath = _namespaces.copyUpdate(namespaces or {}).xpath
        self._should = _init(should)
        self._could = _init(could)

    def add(self, identifier, partname=None, lxmlNode=None):
        if not identifier:
            raise ValueError("Empty identifier not allowed.")
        self.ctx.tx.locals['id'] = identifier
        for partSpec in self._should:
            shouldPartname = partSpec['partname']
            partXPath = partSpec['xpath']
            asData = partSpec['asData']
            part = self._findPart(identifier, shouldPartname, lxmlNode, partXPath, asData)
            if part == None:
                raise VenturiException("Expected '%s', '%s'" % (shouldPartname, partXPath))
            kwargs = dict(identifier=identifier, partname=shouldPartname)
            kwargs['data' if asData else 'lxmlNode'] = part
            yield self.all.add(**kwargs)
        for partSpec in self._could:
            couldPartname = partSpec['partname']
            partXPath = partSpec['xpath']
            asData = partSpec['asData']
            part = self._findPart(identifier, couldPartname, lxmlNode, partXPath, asData)
            if part != None:
                kwargs = dict(identifier=identifier, partname=couldPartname)
                kwargs['data' if asData else 'lxmlNode'] = part
                yield self.all.add(**kwargs)

    def delete(self, identifier):
        if not identifier:
            raise ValueError("Empty identifier not allowed.")
        self.ctx.tx.locals['id'] = identifier
        yield self.all.delete(identifier=identifier)

    def _findPart(self, identifier, partname, lxmlNode, partXPath, asData):
        matches = self.xpath(lxmlNode, partXPath)
        if len(matches) > 1:
            raise VenturiException("XPath '%s' should return atmost one result." % partXPath)
        if len(matches) == 1:
            return self._elementOrText2Text(matches[0]) if asData else self._nodeOrText2ElementTree(matches[0])
        try:
            data = self.call.getData(identifier=identifier, name=partname)
            return data if asData else ElementTree(XML(data))
        except KeyError:
            return None

    def _nodeOrText2ElementTree(self, nodeOrText):
        if type(nodeOrText) == _Element:
            return ElementTree(lxmlElementUntail(nodeOrText))
        return ElementTree(XML(nodeOrText))

    def _elementOrText2Text(self, elementOrText):
        if type(elementOrText) == _Element:
            return lxmltobytes(elementOrText)
        return ensureBytes(elementOrText)


mandatoryKeys = ['partname', 'xpath']
optionalKeys = ['asData']
def _init(venturiList):
    if venturiList is None:
        return []
    result = []
    for item in venturiList:
        if type(item) is tuple:
            result.append(dict(partname=item[0], xpath=item[1], asString=False))
            warn("Please use {'partname':'...', 'xpath':'...', 'asString':False}", DeprecationWarning)
        else:
            if 'asString' in item:
                item['asData'] = item.pop('asString')
                warn("Please use 'asData':... instead of 'asString'", DeprecationWarning)
            if not 'asData' in item:
                item['asData'] = False
            assert set(item.keys()) == set(mandatoryKeys + optionalKeys), "Expected the following keys: %s" % ', '.join(mandatoryKeys)
            result.append(item)
    return result


class VenturiException(Exception):
    pass
