
from cq2utils import CQ2TestCase, CallTrace

from merescocore.framework import Transaction
from merescocomponents.ngram import NGramIndex
from merescocomponents.ngram.ngram import NGRAMS_FIELD, NAME_FIELD

class NGramIndexTest(CQ2TestCase):
    def testIndexOneField(self):
        __callstack_var_tx__ = Transaction('record')
        index = CallTrace('index')
        ngramindex = NGramIndex(transactionName='record')
        ngramindex.addObserver(index)
        
        ngramindex.begin()
        ngramindex.addField('fieldname', 'value')

        self.assertEquals([], [m.name for m in index.calledMethods])
        
        ngramindex.commit()
        
        self.assertEquals(['addDocument'], [m.name for m in index.calledMethods])
        doc = index.calledMethods[0].args[0]
        self.assertEquals('value$', doc.identifier)
        self.assertEquals(['va al lu ue'], doc.asDict()['ngrams'])
        
    def testIndexMultipleField(self):
        __callstack_var_tx__ = Transaction('record')
        index = CallTrace('index')
        ngramindex = NGramIndex(transactionName='record')
        ngramindex.addObserver(index)

        ngramindex.begin()
        ngramindex.addField('field0', 'value')
        ngramindex.addField('field1', 'value')
        ngramindex.addField('field2', 'value3')

        self.assertEquals([], [m.name for m in index.calledMethods])

        ngramindex.commit()

        self.assertEquals(['addDocument', 'addDocument'], [m.name for m in index.calledMethods])
        docIds = [doc.identifier for doc in (m.args[0] for m in index.calledMethods)]
        self.assertEquals(set(['value$', 'value3$']), set(docIds))

    def testIndexFields(self):
        __callstack_var_tx__ = Transaction('record')
        index = CallTrace('index')
        ngramindex = NGramIndex(transactionName='record', fieldnames=['field2'])
        ngramindex.addObserver(index)

        ngramindex.begin()
        ngramindex.addField('field0', 'value')
        ngramindex.addField('field1', 'value')
        ngramindex.addField('field2', 'value3')

        self.assertEquals([], [m.name for m in index.calledMethods])

        ngramindex.commit()

        self.assertEquals(['addDocument', 'addDocument', 'addDocument'], [m.name for m in index.calledMethods])
        docs = [(doc.identifier, doc.asDict()[NGRAMS_FIELD][0], doc.asDict()[NAME_FIELD][0]) for doc in (m.args[0] for m in index.calledMethods)]
        docs.sort()
        self.assertEquals(('value$', 'va al lu ue', 'ngrams$'), docs[0])
        self.assertEquals(('value3$', 'va al lu ue e3', 'ngrams$'), docs[1])
        self.assertEquals(('value3$field2', 'va al lu ue e3', 'ngrams$field2'), docs[2])
        
