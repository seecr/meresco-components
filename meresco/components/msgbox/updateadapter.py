## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
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

from meresco.core import Observable
from lxml.etree import parse
from os.path import basename
from xml.sax.saxutils import escape as xmlEscape

class UpdateAdapterFromMsgbox(Observable):

    def add(self, filename, filedata):
        lxmlNode = parse(filedata)
        if len(lxmlNode.xpath("/delete")) > 0:
            self.do.delete(identifier=filename, lxmlNode=lxmlNode)
        else:
            self.do.add(identifier=filename, lxmlNode=lxmlNode)

class UpdateAdapterToMsgbox(Observable):

    def add(self, identifier, partName, data):
        return self.all.add(filename='%s.add' % identifier, filedata=data)

    def delete(self, identifier):
        return self.all.add(filename='%s.delete' % identifier, filedata='')

