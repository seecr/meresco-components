# -*- coding: utf-8 -*-

from os.path import join, isfile

from cq2utils import CQ2TestCase
from merescocomponents.facetindex.tools import unlock

class LuceneToolsTest(CQ2TestCase):
    def testUnlockNoFilesPresent(self):
        unlock(self.tempdir)

    def testUnlockNoLockPresent(self):
        open(join(self.tempdir, "afile"), "w").close()
        unlock(self.tempdir)

    def testUnlock(self):
        lockFile = join(self.tempdir, "write.lock")
        open(lockFile, "w").close()
        self.assertTrue(isfile(lockFile))
        unlock(self.tempdir)
        self.assertFalse(isfile(lockFile))

    def testUnlockWithFilesOpen(self):
        lockFile = join(self.tempdir, "write.lock")
        open(lockFile, "w").close()
        afile = join(self.tempdir, "afile")
        openFile = open(afile, "w")

        try:
            unlock(self.tempdir)
        except Exception, e:
            self.assertTrue(str(e).startswith("Refusing to remove Lucene lock"))
            self.assertTrue("/afile" in str(e))
        finally:
            openFile.close()
        self.assertTrue(isfile(lockFile))

        unlock(self.tempdir)
        self.assertFalse(isfile(lockFile))