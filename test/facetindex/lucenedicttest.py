# -*- coding: utf-8 -*-


from cq2utils import CQ2TestCase

from merescocomponents.facetindex import LuceneDict

class LuceneDictTest(CQ2TestCase):
    def testInsert(self):
        d = LuceneDict(self.tempdir)
        d['1'] = 'some string'
        self.assertEquals('some string', d['1'])
        d['1'] = 'some other string'
        self.assertEquals('some other string', d['1'])
        self.assertEquals(1, len(d))

    def testNoneExistingKey(self):
        d = LuceneDict(self.tempdir)
        try:
            d['not']
            self.fail()
        except KeyError:
            pass

    def testDelete(self):
        d = LuceneDict(self.tempdir)
        d['1'] = 'some other string'
        self.assertEquals(1, len(d))
        del d['1']
        self.assertEquals(0, len(d))

    def testHasKey(self):
        d = LuceneDict(self.tempdir)
        d['1'] = 'some other string'

        self.assertFalse('2' in d)
        self.assertTrue('1' in d)
        self.assertTrue('2' not in d)
        self.assertFalse(d.has_key('2'))
        self.assertTrue(d.has_key('1'))

    def testGet(self):
        d = LuceneDict(self.tempdir)
        d['1'] = 'some other string'

        self.assertEquals('some other string', d.get('1', 'something'))
        self.assertEquals('something', d.get('2', 'something'))

    def testSetdefault(self):
        d = LuceneDict(self.tempdir)
        self.assertEquals('default', d.setdefault('1', 'default'))
        self.assertEquals('default', d.setdefault('1', 'other'))
        self.assertEquals('default', d['1'])
        d['2'] = 'value'
        self.assertEquals('value', d.setdefault('2', 'default'))

    def testItemsKeysValues(self):
        d = LuceneDict(self.tempdir)
        d['1'] = 'one'
        d['2'] = 'two'
        self.assertEquals(set(['1','2']), set(d.keys()))
        self.assertEquals(set(['one','two']), set(d.values()))
        self.assertEquals(set([('1','one'),('2','two')]), set(d.items()))
        

#items()¶
#keys()¶
#values()¶
