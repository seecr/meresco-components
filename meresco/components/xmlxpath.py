## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010, 2012 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012-2014, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from copy import copy
from io import StringIO
from lxml.etree import ElementTree

from meresco.core import Observable
from warnings import warn
from meresco.xml.namespaces import namespaces as _namespaces


#HM: To support both lxml1.2 as 2.1
try:
    from lxml.etree import _ElementStringResult, _ElementUnicodeResult
except ImportError:
    _ElementStringResult = str
    _ElementUnicodeResult = str

oftenUsedNamespaces = _namespaces.copyUpdate(dict(
    lom="http://ltsc.ieee.org/xsd/LOM",
))

class XmlXPath(Observable):
    def __init__(self, xpathList, fromKwarg, toKwarg=None, namespaces=None, namespaceMap=None):
        Observable.__init__(self)
        self._xpaths = xpathList
        self._fromKwarg = fromKwarg
        self._toKwarg = toKwarg if toKwarg else self._fromKwarg
        if namespaceMap:
            warn("Please use 'namespaces=...'", DeprecationWarning)
            namespaces = namespaceMap
        self.xpath = oftenUsedNamespaces.copyUpdate(namespaces or {}).xpath

    def do_unknown(self, msg, *args, **kwargs):
        for newArgs, newKwargs in self._convertArgs(*args, **kwargs):
            self.do.unknown(msg, *newArgs, **newKwargs)

    def all_unknown(self, msg, *args, **kwargs):
        for newArgs, newKwargs in self._convertArgs(*args, **kwargs):
            yield self.all.unknown(msg, *newArgs, **newKwargs)

    def _convertArgs(self, *args, **kwargs):
        oldvalue = kwargs[self._fromKwarg]
        del kwargs[self._fromKwarg]
        for newTree in self._findNewTree(oldvalue):
            kwargs[self._toKwarg] = newTree
            yield args, kwargs
        return

    def _findNewTree(self, elementTree):
        for xpath in self._xpaths:
            for element in self.xpath(elementTree, xpath):
                if type(element) in [_ElementStringResult, _ElementUnicodeResult, str, str]:
                    yield element
                else:
                    yield ElementTree(lxmlElementUntail(element))


def lxmlElementUntail(element):
    """Utility that works around a problem in lxml.
Should be applied to Elements that are taken out of one ElementTree to be wrapped in a new ElementTree and fed to an XSLT transformation (which would otherwise sometimes segfault)."""

    if not element.tail is None:
        element = copy(element)
        element.tail = None
    return element

