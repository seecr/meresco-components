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

class WrapIterable(object):
    def __init__(self, iterable):
        self._iterator = iter(iterable)
    
    def __iter__(self):
        return self

    def next(self):
        return self._iterator.next()

class PeekIterator(object):
    def __init__(self, iterable):
        self._iterator = iter(iterable)
        self._next = None

    def __iter__(self):
        return self

    def peek(self):
        if self._next == None:
            self._next = self._iterator.next()
        if self._next == None:
            raise StopIteration()
        return self._next

    def hasNext(self):
        try:
            self.peek()
            return True
        except StopIteration:
            return False

    def next(self):
        if self._next != None:
            try:
                return self._next
            finally:
                self._next = None
        return self._iterator.next()

class PairIterator(object):
    def __init__(self, lhs, rhs):
        self._lhs = PeekIterator(lhs)
        self._rhs = PeekIterator(rhs)

    def __iter__(self):
        return self

class OrIterator(PairIterator):
    def next(self):
        if not self._lhs.hasNext():
            return self._rhs.next()
        if not self._rhs.hasNext():
            return self._lhs.next()
        if self._lhs.peek() < self._rhs.peek():
            return self._lhs.next()
        if self._lhs.peek() == self._rhs.peek():
            self._lhs.next()
        return self._rhs.next()

class AndIterator(PairIterator):
    def next(self):
        while self._lhs.peek() != self._rhs.peek():
            while self._lhs.peek() < self._rhs.peek():
                self._lhs.next()
            while self._rhs.peek() < self._lhs.peek():
                self._rhs.next()
        return self._rhs.next()
