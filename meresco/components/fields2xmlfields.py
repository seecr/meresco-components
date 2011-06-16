## begin license ##
# 
# "Edurep" is a service for searching in educational repositories.
# "Edurep" is developed for Stichting Kennisnet (http://www.kennisnet.nl) by
# Seek You Too (http://www.cq2.nl). The project is based on the opensource
# project Meresco (http://www.meresco.com). 
# 
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# 
# 
# This file is part of "Edurep"
# 
# "Edurep" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Edurep" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Edurep"; if not, write to the Free Software
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
        self.txs = {}

    def begin(self):
        tx = self.ctx.tx
        if tx.name != self._transactionName:
            return
        tx.join(self)
        self.txs[tx.getId()] = []

    def addField(self, name, value):
        tx = self.ctx.tx
        self.txs[tx.getId()].append((name, value))

    def commit(self):
        tx = self.ctx.tx
        fields = self.txs.pop(tx.getId())
        if not fields:
            return
        
        ns = self._namespace != None and ' xmlns="%s"' % self._namespace or ''
        xml = '<fields%s>%s</fields>' % (ns, generateXml(fields))
        self.do.add(identifier=tx.locals["id"], partname=self._partname, data=xml)

def _generateXml(fields):
    for (key, value) in fields:
        yield """<field name="%s">%s</field>""" % (_escapeXml(key), _escapeXml(value))

def _escapeXml(value):
    return escapeXml(value).replace('"', "&quot;")

def generateXml(fields):
    return ''.join(_generateXml(fields))
