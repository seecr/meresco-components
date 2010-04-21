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

from meresco.core import Observable
from lxml.etree import ElementTree, _ElementTree as ElementTreeType, parse
from StringIO import StringIO

oftenUsedNamespaces = {
    'oai_dc': "http://www.openarchives.org/OAI/2.0/oai_dc/",
    'dc': "http://purl.org/dc/elements/1.1/",
    'oai': "http://www.openarchives.org/OAI/2.0/",
    'lom': "http://ltsc.ieee.org/xsd/LOM",
    'meta': "http://meresco.org/namespace/harvester/meta",
}

class XmlXPath(Observable):
    def __init__(self, xpathList, namespaceMap = {}):
        Observable.__init__(self)
        self._xpaths = xpathList
        self._namespacesMap = oftenUsedNamespaces.copy()
        self._namespacesMap.update(namespaceMap)

    def unknown(self, msg, *args, **kwargs):
        changeTheseArgs = [(position,arg) for position,arg in enumerate(args) if type(arg) == ElementTreeType]
        changeTheseKwargs = [(key,value) for key,value in kwargs.items() if type(value) == ElementTreeType]
        assert len(changeTheseArgs) + len(changeTheseKwargs) <= 1, 'Can only handle one ElementTree in argument list.'

        if changeTheseArgs:
            position, elementTree = changeTheseArgs[0]
            for newTree in self._findNewTree(elementTree):
                newArgs = [arg for arg in args]
                newArgs[position] = newTree
                yield self.all.unknown(msg, *newArgs, **kwargs)
        elif changeTheseKwargs:
            key, elementTree = changeTheseKwargs[0]
            for newTree in self._findNewTree(elementTree):
                newKwargs = kwargs.copy()
                newKwargs[key] = newTree
                yield self.all.unknown(msg, *args, **newKwargs)
        else:
            yield self.all.unknown(msg, *args, **kwargs)

    def _findNewTree(self, elementTree):
        for xpath in self._xpaths:
            for element in elementTree.xpath(xpath, namespaces=self._namespacesMap):
                #to fix root element:
                buffer = StringIO()
                ElementTree(element).write(buffer)
                buffer.seek(0)
                yield parse(buffer)
