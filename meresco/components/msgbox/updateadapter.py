## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
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

class UpdateAdapterFromMsgbox(Observable):

    def add(self, identifier, filedata):
        identifier, extension = identifier.rsplit('.', 1)
        if extension == "delete":
            yield self.all.delete(identifier=identifier)
        elif extension == "add":
            yield self.all.add(identifier=identifier, partname=None, filedata=filedata)
        else:
            raise ValueError('Expected add or delete as file extension')

class UpdateAdapterToMsgbox(Observable):

    def add(self, identifier, data, **kwargs):
        yield self.all.add(identifier='%s.add' % identifier, filedata=data, **kwargs)

    def delete(self, identifier):
        yield self.all.add(identifier='%s.delete' % identifier, filedata='')

