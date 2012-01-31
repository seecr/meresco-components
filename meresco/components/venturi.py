## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from lxml.etree import _Element, ElementTree, parse, XMLParser
from StringIO import StringIO

from meresco.core import Observable

from meresco.components.xmlxpath import lxmlElementUntail


class Venturi(Observable):
    def __init__(self, should=[], could=[], namespaceMap={}):
        Observable.__init__(self)
        self._namespaceMap = namespaceMap
        self._should = should
        self._could = could

    def add(self, identifier, partname=None, lxmlNode=None):
        if not identifier:
            raise ValueError("Empty identifier not allowed.")
        self.ctx.tx.locals['id'] = identifier
        for shouldPartname, partXPath in self._should:
            part = self._findPart(identifier, shouldPartname, lxmlNode, partXPath)
            if part == None:
                raise VenturiException("Expected '%s', '%s'" % (shouldPartname, partXPath))
            yield self.all.add(identifier=identifier, partname=shouldPartname, lxmlNode=part)
        for couldPartname, partXPath in self._could:
            part = self._findPart(identifier, couldPartname, lxmlNode, partXPath)
            if part != None:
                yield self.all.add(identifier=identifier, partname=couldPartname, lxmlNode=part)

    def delete(self, identifier):
        if not identifier:
            raise ValueError("Empty identifier not allowed.")
        self.ctx.tx.locals['id'] = identifier
        yield self.all.delete(identifier=identifier)

    def _findPart(self, identifier, partname, lxmlNode, partXPath):
        matches = lxmlNode.xpath(partXPath, namespaces=self._namespaceMap)
        if len(matches) > 1:
            raise VenturiException("XPath '%s' should return atmost one result." % partXPath)
        if len(matches) == 1:
            return self._nodeOrText2ElementTree(matches[0])
        if self.call.isAvailable(identifier, partname) == (True, True):
            return parse(self.call.getStream(identifier, partname))
        return None

    def _nodeOrText2ElementTree(self, nodeOrText):
        if type(nodeOrText) == _Element:
            return ElementTree(lxmlElementUntail(nodeOrText))
        return parse(StringIO(nodeOrText))


class VenturiException(Exception):
    pass
