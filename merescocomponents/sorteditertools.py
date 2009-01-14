
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