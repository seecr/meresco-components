# -*- coding: utf-8 -*-

from os.path import join, isfile

from cq2utils import CQ2TestCase
from merescocomponents.facetindex.tools import unlock
from merescocomponents.facetindex.tools.lucenetools import _assertNoFilesOpenInPath

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

    def testAssertNoFilesOpenInPathLsofError(self):
        try:
            _assertNoFilesOpenInPath("dummy", lsofFunc=lambda path: ("dummy cmdline", "", "Some Error", 1))
            self.fail()
        except Exception, e:
            self.assertEquals("'dummy cmdline' failed:\nSome Error", str(e))

    def testAssertNoFilesOpenInPathLsofWarning(self):
        _assertNoFilesOpenInPath("dummy", lsofFunc=lambda path: ("dummy cmdline", "", "WARNING: some warning", 1))