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

from re import compile
from StringIO import StringIO
from xml.sax.saxutils import escape as escapeXml

correctNameRe = compile(r'^\w+$')

class Fields2XmlTx(Observable):
    def __init__(self, resourceManager, partName, namespace=None):
        Observable.__init__(self)
        if not correctNameRe.match(partName):
            raise Fields2XmlException('Invalid name: "%s"' % partName)
        self._identifier = None
        self._fields = []
        self._partName = partName
        self._resourceManager = resourceManager
        self._namespace = namespace

    def addField(self, name, value):
        self._fields.append((name,value))

    def commit(self):
        ns = self._namespace != None and ' xmlns="%s"' % self._namespace or ''
        xml = '<%s%s>%s</%s>' % (self._partName, ns, generateXml(self._fields), self._partName)

        identifier = self._resourceManager.ctx.tx.locals['id']
        self._resourceManager.do.store(identifier, self._partName, xml)

def splitName(name):
    result = name.split('.')
    return '//' + '/'.join(result[:-1]), result[-1]

def _generateXml(fields):
    currentPath = '//'
    for name, value in fields:
        for namePart in name.split('.'):
            if not correctNameRe.match(namePart):
                raise Fields2XmlException('Invalid name: "%s"' % name)

        parentPath, tagName = splitName(name)
        while parentPath != currentPath:
            if currentPath in parentPath:
                parentTagsToAdd = [tag for tag in parentPath[len(currentPath):].split('/') if tag]
                for tag in parentTagsToAdd:
                    yield '<%s>' % tag
                currentPath = parentPath
            else:
                tag = currentPath.split('/')[-1]
                currentPath = '/'.join(currentPath.split('/')[:-1])
                yield '</%s>' % tag
        yield '<%s>%s</%s>' % (tagName, escapeXml(value), tagName)
    if currentPath != '//':
        parentTagsToRemove = currentPath[len('//'):].split('/')
        for tag in reversed(parentTagsToRemove):
            yield '</%s>' % tag

def generateXml(fields):
    return ''.join(_generateXml(fields))

class Fields2XmlException(Exception):
    pass
