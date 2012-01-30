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
# Copyright (C) 2010, 2012 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.components import Converter
from amara.binderytools import bind_string
from amara.bindery import is_element
from lxml.etree import parse, _ElementTree, tostring, _XSLTResultTree
from cStringIO import StringIO
from re import compile

try:
    from lxml.etree import _ElementStringResult, _ElementUnicodeResult
except:
    _ElementStringResult = str
    _ElementUnicodeResult = unicode

xmlStringRegexp = compile(r'(?s)^\s*<.*>\s*$')
def isXmlString(anObject):
    return type(anObject) in [str, _ElementStringResult, unicode, _ElementUnicodeResult] and xmlStringRegexp.match(anObject)

class XmlParseAmara(Converter):
    def _canConvert(self, anObject):
        return isXmlString(anObject)

    def _convert(self, anObject):
        return bind_string(anObject.encode('UTF-8')).childNodes[0]

class XmlPrintAmara(Converter):
    def _canConvert(self, anObject):
        return is_element(anObject)

    def _convert(self, anObject):
        return anObject.xml()

class FileParseLxml(Converter):
    def _canConvert(self, anObject):
        return hasattr(anObject, 'read') and hasattr(anObject, 'readline')

    def _convert(self, anObject):
        return parse(anObject)

class XmlParseLxml(Converter):
    def _canConvert(self, anObject):
        return isXmlString(anObject)

    def _convert(self, anObject):
        return parse(StringIO(anObject.encode('UTF-8')))
        
class XmlPrintLxml(Converter):
    def _canConvert(self, anObject):
        return type(anObject) == _ElementTree

    def _convert(self, anObject):
        return tostring(anObject, pretty_print = True, encoding="UTF-8")

class Amara2Lxml(Converter):
    def _canConvert(self, anObject):
        return is_element(anObject)

    def _convert(self, anObject):
        return parse(StringIO(anObject.xml()))

class Lxml2Amara(Converter):
    def _canConvert(self, anObject):
        return type(anObject) in [_ElementTree, _XSLTResultTree]

    def _convert(self, anObject):
        return bind_string(tostring(anObject, encoding="UTF-8")).childNodes[0]

# backwards compatible
XmlInflate = XmlParseAmara
XmlDeflate = XmlPrintAmara
