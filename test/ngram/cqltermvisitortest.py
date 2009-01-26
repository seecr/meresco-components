
from unittest import TestCase
from merescocomponents.cqltermvisitor import CqlTermVisitor
from cqlparser import parseString

class CqlTermVisitorTest(TestCase):

    def assertTermVisitor(self, expectedList, cqlstring):
        self.assertEquals(expectedList, CqlTermVisitor(parseString(cqlstring)).visit())

    def testCqlTermVisitor(self) :
        self.assertTermVisitor(['word0'], 'word0')
        self.assertTermVisitor(['word0', 'word1'], 'word0 and word1')
        self.assertTermVisitor(['word0', 'word1', 'word2'], 'word0 and ( word1 and word2 )')
        self.assertTermVisitor([], 'field = value')
        self.assertTermVisitor(['word0'], 'word0 and (field = value)')
        
