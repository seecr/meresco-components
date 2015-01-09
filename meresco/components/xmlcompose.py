## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
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

from meresco.core import Observable
from lxml.etree import parse
from xml.sax.saxutils import escape as xmlEscape

class XmlCompose(Observable):
    def __init__(self, template, nsMap, **fieldMapping):
        Observable.__init__(self)
        self._template = template
        self._nsMap = nsMap
        self._fieldMapping = fieldMapping
    
    def getRecord(self, identifier):
        data = {}
        cachedRecord = {}
        for tagName, values in list(self._fieldMapping.items()):
            partname, xPathExpression = values
            if not partname in cachedRecord:
                cachedRecord[partname] = self._getPart(identifier, partname)
            xml = cachedRecord[partname]
            result = xml.xpath(xPathExpression, namespaces=self._nsMap)
            if result:
                data[tagName] = str(result[0])
        return self.createRecord(data)

    def createRecord(self, data):
        if len(data) != len(self._fieldMapping):
            return '' 
        return self._template % dict(((k, xmlEscape(v)) for k,v in list(data.items())))

    def _getPart(self, identifier, partname):
        return parse(self.call.getStream(identifier, partname))
