
from cq2utils import CQ2TestCase
from os.path import join

from merescocomponents import SortedFileList

class SortedFileListTest(CQ2TestCase):
    def testAppendAndWrite(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        s.append(1)
        s.append(2)
        self.assertEquals([1,2], list(iter(s)))
        s.close()
        self.assertEquals('1\n2\n', open(join(self.tempdir, 'list')).read())
        self.assertEquals([1,2], list(s))
        s = SortedFileList(join(self.tempdir, 'list'))
        self.assertEquals([1,2], list(s))

    def testRewrite(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        for i in range(20):
            s.append(i)
        s = SortedFileList(join(self.tempdir, 'list'), (i for i in s if i%2 == 0))
        self.assertEquals([0,2,4,6,8,10,12,14,16,18], list(s))

    def testEmpty(self):
        s = SortedFileList(join(self.tempdir, 'list'))
        self.assertEquals([], list(s))