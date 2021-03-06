## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
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
from xml.sax.saxutils import escape as escapeXml

class Fields2XmlFields(Observable):

    def __init__(self, transactionName, partname, namespace=None):
        Observable.__init__(self)
        self._transactionName = transactionName
        self._partname = partname
        self._namespace = namespace

    def begin(self, name):
        if name != self._transactionName:
            return
        tx = self.ctx.tx
        tx.join(self)

    def addField(self, name, value):
        tx = self.ctx.tx
        tx.objectScope(self).setdefault('fields', []).append((name, value))

    def commit(self, id):
        tx = self.ctx.tx
        fields = tx.objectScope(self).get('fields')
        if not fields:
            return

        ns = self._namespace != None and ' xmlns="%s"' % self._namespace or ''
        xml = '<fields%s>%s</fields>' % (ns, generateXml(fields))
        yield self.all.add(identifier=tx.locals["id"], partname=self._partname, data=xml)

def _generateXml(fields):
    for (key, value) in fields:
        yield """<field name="%s">%s</field>""" % (_escapeXml(key), _escapeXml(value))

def _escapeXml(value):
    return escapeXml(value).replace('"', "&quot;")

def generateXml(fields):
    return ''.join(_generateXml(fields))

