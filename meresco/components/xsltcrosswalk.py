## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
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
from meresco.core import Observable

from lxml.etree import parse, XSLT, _ElementTree, tostring

class XsltCrosswalk(Observable):

    def __init__(self, xslFileList):
        Observable.__init__(self)
        self._xsltFilelist = xslFileList
        self._xslts = None

    def lazyInit(self):
        #xslts are created via _convert (not __init__) due to a bug in XSLT that causes a glibc crash
        #if __init__ is called from a different thread, this might happen. This is a scenario that happens in the integrationtest.

        if self._xslts == None:
            self._xslts = [XSLT(parse(open(s))) for s in self._xsltFilelist]

    def _convert(self, xmlSource):
        self.lazyInit()
        result = xmlSource
        for xslt in self._xslts:
            result = xslt(result)
        return result.getroot().getroottree()

    def _detectAndConvert(self, anObject):
        result = anObject
        if type(anObject) == _ElementTree:
            result = self._convert(anObject)
        return result

    def unknown(self, method, *args, **kwargs):
        newArgs = [self._detectAndConvert(arg) for arg in args]
        newKwargs = dict((key, self._detectAndConvert(value)) for key, value in kwargs.items())
        return self.all.unknown(method, *newArgs, **newKwargs)
