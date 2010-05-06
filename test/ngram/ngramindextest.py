## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2008-2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2008-2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2008-2010 Seek You Too (CQ2) http://www.cq2.nl
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

from cq2utils import CQ2TestCase, CallTrace

from meresco.core import Transaction
from meresco.components.ngram import NGramIndex
from meresco.components.ngram.ngram import NGRAMS_FIELD, NAME_FIELD

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
        self.assertEquals(['va', 'al', 'lu', 'ue'], doc.asDict()['ngrams'])
        
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
        docs = [(doc.identifier, ' '.join(doc.asDict()[NGRAMS_FIELD]), doc.asDict()[NAME_FIELD][0]) for doc in (m.args[0] for m in index.calledMethods)]
        docs.sort()
        self.assertEquals(('value$', 'va al lu ue', 'ngrams$'), docs[0])
        self.assertEquals(('value3$', 'va al lu ue e3', 'ngrams$'), docs[1])
        self.assertEquals(('value3$field2', 'va al lu ue e3', 'ngrams$field2'), docs[2])
        
