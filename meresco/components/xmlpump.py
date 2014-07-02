# -*- coding: utf-8 -*-
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
# Copyright (C) 2012-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012, 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from StringIO import StringIO
from lxml.etree import parse, tostring, XMLParser

from converter import Converter
from re import compile as compileRe


def lxmltostring(lxmlNode, **kwargs):
    return _fixLxmltostringRootElement(tostring(lxmlNode, encoding="UTF-8", **kwargs))


class FileParseLxml(Converter):
    def _convert(self, anObject):
        return parse(anObject)


class XmlParseLxml(Converter):
    def __init__(self, parseOptions=None, **kwargs):
        """When provided, parserOptions must contain arguments to lxml.etree.XMLParser,
e.g. parserOptions=dict(huge_tree=True, remove_blank_text=True)"""
        Converter.__init__(self, **kwargs)
        self._parseOptions = parseOptions

    def _convert(self, anObject):
        parseKwargs = {}
        if not self._parseOptions is None:
            parseKwargs = dict(parser=XMLParser(**self._parseOptions))
        return parse(StringIO(anObject.encode('UTF-8')), **parseKwargs)


class XmlPrintLxml(Converter):
    def __init__(self, pretty_print=True, **kwargs):
        Converter.__init__(self, **kwargs)
        self._pretty_print = pretty_print

    def _convert(self, anObject):
        return lxmltostring(anObject, pretty_print=self._pretty_print)


_CHAR_REF = compileRe(r'\&\#(?P<code>x?[0-9a-fA-F]+);')
def _replCharRef(matchObj):
    code = matchObj.groupdict()['code']
    code = int(code[1:], base=16) if 'x' in code else int(code)
    return str(unichr(code))

def _fixLxmltostringRootElement(aString):
    firstGt = aString.find('>')
    if aString.find('&#', 0, firstGt) > -1:
        return _CHAR_REF.sub(_replCharRef, aString[:firstGt]) + aString[firstGt:]
    return aString
