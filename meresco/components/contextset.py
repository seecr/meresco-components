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

class ContextSet(object):
    def __init__(self, name, aStream):
        self.name = name
        self._dictionary = {}
        self._readStream(aStream)

    def _readStream(self, aStream):
        for k,v in (line.strip().split() for line in aStream if line.strip() and not line.startswith('#')):
            if k not in self._dictionary:
                self._dictionary[k] = v

    def match(self, field):
        return '.' in field and field.split('.',1)[0] == self.name and field.split('.',1)[1] in self._dictionary

    def lookup(self, field):
        if not self.match(field):
            return field
        return self._dictionary[field.split('.',1)[1]]

class ContextSetException(Exception):
    pass

class ContextSetList(object):
    def __init__(self):
        self._contextsets = {}

    def lookup(self, field):
        if '.' not in field:
            return field
        context = field.split('.')[0]
        if context not in self._contextsets:
            return field
        set = self._contextsets[context]
        if set.match(field):
            return set.lookup(field)
        return field

    def add(self, contextSet):
        self._contextsets[contextSet.name] = contextSet
