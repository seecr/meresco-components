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

from re import compile
from StringIO import StringIO
from xml.sax.saxutils import escape as escapeXml

correctNameRe = compile(r'^\w+$')

class Fields2Xml(Observable):
    def __init__(self, partName, namespace=None):
        Observable.__init__(self)
        if not correctNameRe.match(partName):
            raise Fields2XmlException('Invalid name: "%s"' % partName)
        self._identifier = None
        self._partName = partName
        self._namespace = namespace

    def beginTransaction(self):
        raise StopIteration(Fields2Xml.Fields2XmlTx(self, self._partName, self._namespace))
        yield

    class Fields2XmlTx(object):
        def __init__(self, resource, partName, namespace):
            self._fields = []
            self._partName = partName
            self._namespace = namespace
            self._resource = resource

        def addField(self, name, value):
            self._fields.append((name, value))

        def commit(self):
            if not self._fields:
                return
            ns = self._namespace != None and ' xmlns="%s"' % self._namespace or ''
            xml = '<%s%s>%s</%s>' % (self._partName, ns, generateXml(self._fields), self._partName)

            identifier = self._resource.ctx.tx.locals['id']
            yield self._resource.all.add(identifier=identifier, partname=self._partName, data=xml)

def splitName(name):
    result = name.split('.')
    return '//' + '/'.join(result[:-1]), result[-1]

def _generateXml(fields):
    for (key, value) in fields:
        tags = key.split('.')
        for tag in tags:
            if not correctNameRe.match(tag):                                
                raise Fields2XmlException('Invalid key: "%s"' % key)
        yield ''.join("<%s>" % tag for tag in tags)
        yield escapeXml(value)
        yield ''.join("</%s>" % tag for tag in reversed(tags))

def generateXml(fields):
    return ''.join(_generateXml(fields))

class Fields2XmlException(Exception):
    pass
