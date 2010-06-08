# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.core.observable import Observable
from amara.binderytools import bind_string
from amara.bindery import is_element
from lxml.etree import parse, _ElementTree, tostring, _XSLTResultTree
from cStringIO import StringIO
from re import compile

class Converter(Observable):
    def unknown(self, msg, *args, **kwargs):
        newArgs = [self._detectAndConvert(arg) for arg in args]
        newKwargs = dict((key, self._detectAndConvert(value)) for key, value in kwargs.items())
        return self.all.unknown(msg, *newArgs, **newKwargs)

    def _canConvert(self, anObject):
        raise NotImplementedError()

    def _convert(self, anObject):
        raise NotImplementedError()

    def _detectAndConvert(self, anObject):
        if self._canConvert(anObject):
            return self._convert(anObject)
        return anObject


xmlStringRegexp = compile(r'(?s)^\s*<.*>\s*$')
def isXmlString(anObject):
    return type(anObject) in [str, unicode] and xmlStringRegexp.match(anObject)

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
    def _detectAndConvert(self, something):
        if is_element(something):
            return parse(StringIO(something.xml()))
        return something

class Lxml2Amara(Converter):
    def _canConvert(self, anObject):
        return type(anObject) in [_ElementTree, _XSLTResultTree]

    def _convert(self, anObject):
        return bind_string(tostring(anObject, encoding="UTF-8")).childNodes[0]

# backwards compatible
XmlInflate = XmlParseAmara
XmlDeflate = XmlPrintAmara
