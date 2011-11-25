## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.core import Transparent, Observable

class _Fieldlet(Transparent):
    def __init__(self, method):
        Transparent.__init__(self)
        self._method = method

class FilterFieldValue(_Fieldlet):
    def addField(self, name, value):
        if self._method(value):
            self.do.addField(name=name, value=value)

class FilterField(_Fieldlet):
    def addField(self, name, value):
        if self._method(name):
            self.do.addField(name=name, value=value)

class RenameField(_Fieldlet):
    def addField(self, name, value):
        self.do.addField(name=self._method(name), value=value)

class TransformFieldValue(_Fieldlet):
    def addField(self, name, value):
        newValue = self._method(value)
        if newValue != None:
            self.do.addField(name=name, value=newValue)

class AddField(Observable):
    def __init__(self, name, value):
        Observable.__init__(self)
        self._name = name
        self._value = value

    def add(self, *args, **kwargs):
        self.do.addField(name=self._name, value=self._value)

