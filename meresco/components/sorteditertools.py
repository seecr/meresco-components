## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2012, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

class WrapIterable(object):
    def __init__(self, iterable):
        self._iterator = iter(iterable)
    
    def __iter__(self):
        return self

    def __next__(self):
        return next(self._iterator)

class PeekIterator(object):
    def __init__(self, iterable):
        self._iterator = iter(iterable)
        self._next = None

    def __iter__(self):
        return self

    def peek(self):
        if self._next == None:
            self._next = next(self._iterator)
        if self._next == None:
            raise StopIteration()
        return self._next

    def hasNext(self):
        try:
            self.peek()
            return True
        except StopIteration:
            return False

    def __next__(self):
        if self._next != None:
            try:
                return self._next
            finally:
                self._next = None
        return next(self._iterator)

class PairIterator(object):
    def __init__(self, lhs, rhs):
        self._lhs = PeekIterator(lhs)
        self._rhs = PeekIterator(rhs)

    def __iter__(self):
        return self

class OrIterator(PairIterator):
    def __next__(self):
        if not self._lhs.hasNext():
            return next(self._rhs)
        if not self._rhs.hasNext():
            return next(self._lhs)
        if self._lhs.peek() < self._rhs.peek():
            return next(self._lhs)
        if self._lhs.peek() == self._rhs.peek():
            next(self._lhs)
        return next(self._rhs)

class AndIterator(PairIterator):
    def __next__(self):
        while self._lhs.peek() != self._rhs.peek():
            while self._lhs.peek() < self._rhs.peek():
                next(self._lhs)
            while self._rhs.peek() < self._lhs.peek():
                next(self._rhs)
        return next(self._rhs)
