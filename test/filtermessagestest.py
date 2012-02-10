from seecr.test import SeecrTest, CallTrace

from meresco.core import Observable
from meresco.components import FilterMessages

class FilterMessagesTest(SeecrTest):
    def testOne(self):
        observer1 = CallTrace('observer1')
        observer2 = CallTrace('observer2')
        dna = be((Observable(),
                    (FilterMessages(allowed=['allowed']),
                        observer1
                    )
                    (FilterMessages(allowed=['allowed']),
                        observer2
                    )
                ))

        list(compose(dna.all.allowed()))
        self.assertEquals([], [m.name for m in observer1.calledMethods])
        self.assertEquals(['allowed'], [m.name for m in observer2.calledMethods])

