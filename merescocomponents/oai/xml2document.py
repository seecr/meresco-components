## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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

from merescocomponents.facetindex import Document
from amara import binderytools
from amara.bindery import is_element
from merescocore.framework.observable import Observable

TEDDY_NS = "http://www.cq2.nl/teddy"

class Xml2Document(Observable):

    def unknown(self, methodName, *args, **kwargs):
        return self.all.unknown(methodName, *args, **kwargs)

    def add(self, id, partName, amaraXmlNode):
        return self.all.addDocument(self._create(id, amaraXmlNode))

    def _create(self, documentId, topNode):
        doc = Document(documentId)
        self._indexChild(topNode, doc, '')
        return doc

    def _indexChild(self, aNode, doc, parentName):
        if parentName:
            parentName += '.'
        tagname = parentName + str(aNode.localName)
        value = aNode.xml_child_text
        tokenize = True
        skip = False
        for xpathAttribute in aNode.xpathAttributes:
            if xpathAttribute.namespaceURI == TEDDY_NS:
                if xpathAttribute.localName == 'tokenize':
                    tokenize = str(xpathAttribute.value).lower() != 'false'
                if xpathAttribute.localName == 'skip':
                    skip = str(xpathAttribute.value).lower() == 'true'
                    tagname = ''
        if not skip and str(value).strip():
            doc.addIndexedField(tagname, str(value), tokenize)

        for child in filter(is_element, aNode.childNodes):
            self._indexChild(child, doc, tagname)
