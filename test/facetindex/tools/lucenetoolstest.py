# -*- coding: utf-8 -*-

from os.path import join, isfile

from cq2utils import CQ2TestCase
from meresco.components.facetindex.tools import unlock
from meresco.components.facetindex.tools.lucenetools import _assertNoFilesOpenInPath

class LuceneToolsTest(CQ2TestCase):
    def testUnlockUnexistingDir(self):
        unlock(join(self.tempdir, 'doesntexist'))

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
            _assertNoFilesOpenInPath(self.tempdir, lsofFunc=lambda path: ("dummy cmdline", "", "Some Error", 1))
            self.fail()
        except Exception, e:
            self.assertEquals("'dummy cmdline' failed:\nSome Error", str(e))

    def testAssertNoFilesOpenInPathLsofWarning(self):
        _assertNoFilesOpenInPath(self.tempdir, lsofFunc=lambda path: ("dummy cmdline", "", "WARNING: some warning", 1))

    def testAssertNoFilesOpenInPathLsofNotCalledInCaseDirDoesntExist(self):
        def lsofFunc(path):
            raise Exception("Should not have been called")
        _assertNoFilesOpenInPath(join(self.tempdir, "doesnotexist"), lsofFunc=lsofFunc)
