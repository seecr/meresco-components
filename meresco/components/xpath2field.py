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


class XPath2Field(Observable):
    def __init__(self, attributeXpaths=[], namespaceMap={}, sendAsList=False):
        Observable.__init__(self)
        self._attributeXpaths = attributeXpaths
        self._namespaceMap = namespaceMap
        self._sendAsList = sendAsList

    def add(self, id, partName, lxmlNode):
        for (xpath, dottedDestinationPath) in self._attributeXpaths:
            values = lxmlNode.xpath(xpath, namespaces=self._namespaceMap)
            if self._sendAsList:
                values = [values]
            for value in values:
                self.do.addField(name=dottedDestinationPath, value=value)
