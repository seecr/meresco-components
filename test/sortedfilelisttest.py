
from cq2utils import CQ2TestCase
from os.path import join
from bisect import bisect_left, bisect_right

from merescocomponents import SortedFileList

class SortedFileListTest(CQ2TestCase):
    def testAppendAndWrite(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        s.append(1)
        s.append(2)
        self.assertEquals([1,2], list(iter(s)))
        self.assertEquals(16, len(open(join(self.tempdir, 'list')).read()))
        self.assertEquals([1,2], list(s))
        s = SortedFileList(join(self.tempdir, 'list'))
        self.assertEquals([1,2], list(s))
        self.assertEquals(len(s), len(list(s)))

    def testRewrite(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        for i in range(20):
            s.append(i)
        s = SortedFileList(join(self.tempdir, 'list'), (i for i in s if i%2 == 0))
        self.assertEquals([0,2,4,6,8,10,12,14,16,18], list(s))
        self.assertEquals(len(s), len(list(s)))

    def testEmpty(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        self.assertEquals([], list(s))

    def testContains(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        for i in range(0,20,2):
            s.append(i)
        self.assertTrue(14 in s)
        self.assertFalse(15 in s)
        self.assertFalse(32 in s)

    def testGetItem(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        for i in range(20):
            s.append(i)
        self.assertEquals(2, s[2])
        try:
            s[1234567]
            self.fail('IndexError expected')
        except IndexError,e:
            pass
        self.assertEquals(19, s[-1])
        self.assertEquals(0, s[-20])
        try:
            s[-21]
            self.fail('IndexError expected')
        except IndexError,e:
            pass

    def testSlicing(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        for i in range(6):
            s.append(i)
        self.assertEquals([1,2], list(s[1:3]))
        self.assertEquals([0,1,2,3], list(s[:-2]))
        self.assertEquals([4,5], list(s[-2:]))
        self.assertEquals([0,2], list(s[:4:2]))
        self.assertEquals([5,4,3,2,1,0], list(s[::-1]))
        self.assertEquals([], list(s[4:3]))
        self.assertEquals([0,1,2,3,4,5], list(s[-12345:234567]))
        #self.assertEquals([1,2], list(s[1:3]))