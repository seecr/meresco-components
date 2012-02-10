from seecr.test import SeecrTestCase, CallTrace

from weightless.core import compose, be
from meresco.core import Observable
from meresco.components import FilterMessages


class FilterMessagesTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.observer1 = CallTrace(
            'observer1', 
            emptyGeneratorMethods=['message'], 
            returnValues={
                'function': 41, 
                'gen': (i for i in [41]),
                'noop': None
            }
        )
        self.observer2 = CallTrace(
            'observer2', 
            emptyGeneratorMethods=['message'], 
            returnValues={
                'function': 42, 
                'gen': (i for i in [42]),
                'noop': None
            }
        )
        self.dna = be((Observable(),
            (FilterMessages(disallowed=['message', 'function', 'gen', 'noop']),
                (self.observer1,)
            ),
            (FilterMessages(allowed=['message', 'function', 'gen', 'noop']),
                (self.observer2,)
            )
        ))


    def testAll(self):
        list(compose(self.dna.all.message()))
        self.assertEquals([], [m.name for m in self.observer1.calledMethods])
        self.assertEquals(['message'], [m.name for m in self.observer2.calledMethods])

    def testCall(self):
        self.assertEquals(42, self.dna.call.function())

    def testDo(self):
        self.dna.do.noop()
        self.assertEquals([], [m.name for m in self.observer1.calledMethods])
        self.assertEquals(['noop'], [m.name for m in self.observer2.calledMethods])

    def testAny(self):
        self.assertEquals([42], list(compose(self.dna.any.gen())))

