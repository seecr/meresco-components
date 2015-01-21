# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
#
# This file is part of "Meresco Components"
#
# "Meresco Components" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Components" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Components"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import SeecrTestCase, CallTrace

from meresco.core import Transparent

from weightless.core import be
from weightless.io import Reactor

from os.path import join, isfile, basename
from os import makedirs, rename, listdir, system, chmod, remove
from meresco.components import lxmltobytes
from re import sub
from shutil import rmtree
from stat import S_IXUSR, S_IRUSR, S_IWUSR
from time import sleep
from traceback import format_exc

from meresco.components.msgbox import Msgbox
from meresco.components.msgbox.msgbox import File


DATA = "<record/>"

def failingAddMock(identifier, filedata):
    raise ValueError()
    yield

def addMock(identifier, filedata):
    return
    yield

class MsgboxTest(SeecrTestCase):

    def setUp(self):
        SeecrTestCase.setUp(self)
        self.reactor = Reactor()
        self.observer = CallTrace('Observer', methods={'add': addMock})
        self.inDirectory = join(self.tempdir, 'in')
        self.outDirectory = join(self.tempdir, 'out')
        makedirs(self.inDirectory)
        makedirs(self.outDirectory)

    def testCheckDirectoriesOnCreate(self):
        self.createMsgbox()
        try:
            Msgbox(CallTrace('Reactor'), inDirectory="/no_such_in", outDirectory="/tmp")
            self.fail()
        except ValueError as e:
            self.assertEqual("directory /no_such_in does not exist", str(e))

        try:
            Msgbox(CallTrace('Reactor'), inDirectory="/tmp", outDirectory="/no_such_out")
            self.fail()
        except ValueError as e:
            self.assertEqual("directory /no_such_out does not exist", str(e))

    def testMovedInFileTriggersThings(self):
        self.createMsgbox()
        filename = 'repository:some:identifier:1.record'
        self.moveInRecord(filename=filename)
        self.reactor.step()
        calledMethod = self.observer.calledMethods[0]
        self.assertEqual('add', calledMethod.name)
        self.assertEqual(filename, calledMethod.kwargs['identifier'])
        self.assertEqual(join(self.inDirectory, filename), calledMethod.kwargs['filedata'].name)

    def testAckWrittenToOutOnSuccessfulProcessing(self):
        self.createMsgbox()
        filename = 'repository:some:identifier:1.record'
        self.moveInRecord(filename=filename)
        self.assertEqual(0, len(self.observer.calledMethods))
        self.assertTrue(isfile(join(self.inDirectory, filename)))
        self.assertFalse(isfile(join(self.outDirectory, filename + '.ack')))
        self.reactor.step()
        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertFalse(isfile(join(self.inDirectory, filename)))
        self.assertTrue(isfile(join(self.outDirectory, filename + '.ack')))

    def testProcessRecordsOnCommand(self):
        self.moveInRecord(filename='repo:ident:1.record')
        self.moveInRecord(filename='repo:ident:2.record')
        self.msgbox = Msgbox(self.reactor, inDirectory=self.inDirectory, outDirectory=self.outDirectory)
        self.msgbox.addObserver(self.observer)
        self.assertEqual(set(['repo:ident:1.record', 'repo:ident:2.record']), set(self.listfiles(self.inDirectory)))
        self.msgbox.processInDirectory()
        self.assertEqual(set(['repo:ident:1.record.ack', 'repo:ident:2.record.ack']), set(self.listfiles(self.outDirectory)))

    def testProcessFileErrorHandling(self):
        self.observer.methods['add'] = failingAddMock
        self.createMsgbox()
        self.msgbox._logError = lambda m: None

        filename = 'repository:some:identifier:1.record'
        self.moveInRecord(filename=filename)
        self.msgbox.processFile(filename)
        self.assertFalse(isfile(join(self.inDirectory, filename)))
        errorFile = join(self.outDirectory, filename + '.error')
        self.assertTrue(isfile(errorFile))
        with open(errorFile) as fp:
            errorMessage = fp.read()
            self.assertTrue(errorMessage.startswith("Traceback (most recent call last):"))
            self.assertTrue(errorMessage.endswith("ValueError\n"), errorMessage)

    def testErrorHandlingWithReactorStep(self):
        self.observer.methods['add'] = failingAddMock
        self.createMsgbox()
        self.msgbox._logError = lambda m: None

        filename = 'repo:identifier:1.record'
        self.moveInRecord(filename=filename)
        self.reactor.step()
        self.assertFalse(isfile(join(self.inDirectory, filename)))
        errorFile = join(self.outDirectory, filename + '.error')
        self.assertTrue(isfile(errorFile))
        with open(errorFile) as fp:
            errorMessage = fp.read()
        self.assertTrue(errorMessage.startswith("Traceback (most recent call last):"))
        self.assertTrue(errorMessage.endswith("ValueError\n"), errorMessage)
        self.assertTrue(self.msgbox._watcher in self.reactor._readers)

    def testCreateAsynchronousMsgbox(self):
        self.createMsgbox(asynchronous=True)
        self.assertFalse(self.msgbox._synchronous)

    def testProcessFileInAsynchronousMsgbox(self):
        self.createMsgbox(asynchronous=True)
        filename='repository:some:identifier:1.record'
        self.moveInRecord(filename=filename)

        self.assertEqual(0, len(self.observer.calledMethods))
        self.assertTrue(isfile(join(self.inDirectory, filename)))
        self.assertFalse(isfile(join(self.outDirectory, filename)))
        self.reactor.step()
        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertFalse(isfile(join(self.inDirectory, filename)))
        self.assertFalse(isfile(join(self.outDirectory, filename + '.ack')))

    def testErrorHandlingAsynchronousMsgbox(self):
        self.observer.methods['add'] = failingAddMock
        self.createMsgbox(asynchronous=True)
        self.msgbox._logError = lambda m: None

        filename = 'repo:identifier:1.record'
        self.moveInRecord(filename=filename)
        self.assertTrue(isfile(join(self.inDirectory, filename)))
        self.reactor.step()
        self.assertFalse(isfile(join(self.inDirectory, filename)))
        errorFile = join(self.outDirectory, filename + '.error')
        self.assertTrue(isfile(errorFile))
        with open(errorFile) as fp:
            errorMessage = fp.read()
            self.assertTrue(errorMessage.startswith("Traceback (most recent call last):"))
            self.assertTrue(errorMessage.endswith("ValueError\n"), errorMessage)
        self.assertTrue(self.msgbox._watcher in self.reactor._readers)

    def testAck(self):
        self.createMsgbox(asynchronous=True)
        filename='repository:some:identifier:1.record'
        with open(join(self.inDirectory, filename), 'w') as fp:
            fp.write(DATA)
        self.assertFalse(isfile(join(self.outDirectory, filename + '.ack')))
        self.msgbox._ack(filename)
        self.assertTrue(isfile(join(self.inDirectory, filename)))
        self.assertTrue(isfile(join(self.outDirectory, filename + '.ack')))

    def testError(self):
        self.createMsgbox(asynchronous=True)
        filename='repository:some:identifier:1.record'
        errormessage = "an error occurred"
        errorfile = join(self.outDirectory, filename + '.error')
        with open(join(self.inDirectory, filename), 'w') as fp:
            fp.write(DATA)
        self.assertFalse(isfile(errorfile))
        self.msgbox._error(filename, errormessage)
        self.assertTrue(isfile(join(self.inDirectory, filename)))
        self.assertFalse(isfile(join(self.outDirectory, filename + '.ack')))
        with open(errorfile) as fp:
            self.assertEqual(errormessage, fp.read())

    def testNoFilesInTmpWhenStarting(self):
        filename = "testFile"
        tmpDirectory = join(self.outDirectory, 'tmp')
        makedirs(tmpDirectory)
        open(join(tmpDirectory, filename), 'w').close()
        self.createMsgbox()
        self.assertEqual(0, len(self.listfiles(self.msgbox._tmpDirectory)))

    def testAddWithFilenameAndFiledata(self):
        self.createMsgbox()
        filename = "testfile"
        filedata = DATA
        list(self.msgbox.add(filename, filedata))
        outFiles = self.listfiles(self.outDirectory)
        tmpFiles = self.listfiles(self.msgbox._tmpDirectory)
        self.assertEqual(1, len(outFiles))
        self.assertEqual(0, len(tmpFiles))
        self.assertEqual(filename, outFiles[0])
        with open(join(self.outDirectory, outFiles[0]), 'r') as f:
            self.assertEqual(filedata, f.read())

    def testAddWithFileLikeObject(self):
        self.createMsgbox()
        filename = "testfile"
        filepath = join(self.tempdir, filename)
        with open(filepath, "w") as fp:
            fp.write(DATA)
        with File(filepath) as fp:
            list(self.msgbox.add(filename, fp, ignoredKwarg="e.g. useful to have parsed lxmlNode included in combination with XmlXPath filtering"))
        outFiles = self.listfiles(self.outDirectory)
        self.assertEqual(filename, outFiles[0])
        with open(join(self.outDirectory, outFiles[0]), 'r') as f:
            self.assertEqual(DATA, f.read())

    def testAddWithOpenFile(self):
        self.createMsgbox()
        filename = "testfile"
        filepath = join(self.tempdir, filename)
        with open(filepath, "w") as fp:
            fp.write(DATA)
        with open(filepath) as fp:
            list(self.msgbox.add(filename, fp, ignoredKwarg="e.g. useful to have parsed lxmlNode included in combination with XmlXPath filtering"))
        outFiles = self.listfiles(self.outDirectory)
        self.assertEqual(basename(filepath), outFiles[0])
        with open(join(self.outDirectory, outFiles[0]), 'r') as f:
            self.assertEqual(DATA, f.read())

    # suspicious (old reality)!
    def testDuplicateReplacesOriginal(self):
        self.createMsgbox()
        filename = "testfile"
        list(self.msgbox.add(filename, DATA))
        data2 = "<a>something</a>"
        list(self.msgbox.add(filename, data2))
        outFiles = self.listfiles(self.outDirectory)
        self.assertEqual([filename], outFiles)
        with open(join(self.outDirectory, filename)) as fp:
            self.assertEqual(data2, fp.read())

    # suspicious (old reality)!
    def testExistingAckReplaced(self):
        self.createMsgbox()
        filename = 'repository:some:identifier:1.record'
        self.moveInRecord(filename=filename)
        self.msgbox.processFile(filename)
        self.moveInRecord(filename=filename)
        self.msgbox.processFile(filename)
        self.assertEqual(2, len(self.observer.calledMethods))
        self.assertFalse(isfile(join(self.inDirectory, filename)))
        self.assertTrue(isfile(join(self.outDirectory, filename + '.ack')))
        self.assertFalse(isfile(join(self.outDirectory, filename + '.error')))

    def testNoFilesLeftBehindOnMoveError(self):
        self.createMsgbox()
        filename = "test"
        filedata = DATA
        try:
            chmod(self.outDirectory, S_IRUSR | S_IXUSR)
            self.assertRaises(OSError, lambda: list(self.msgbox.add(filename, filedata)))
            tmpFiles = self.listfiles(self.msgbox._tmpDirectory)
            self.assertEqual(0, len(tmpFiles))
        finally:
            chmod(self.outDirectory, S_IRUSR | S_IWUSR | S_IXUSR)

    def testRaiseErrorWhenOtherFailureThanNotExists(self):
        self.createMsgbox()
        try:
            self.msgbox.processFile(self.tempdir)
            self.fail("Remove a directory should raise an error and not be ignored.")
        except OSError:
            pass

    def testAddSynchronousIsEmptyGenerator(self):
        self.createMsgbox()

        result = self.msgbox.add('filename', 'data')

        self.assertFalse(isfile(join(self.outDirectory, 'filename')))
        self.assertRaises(StopIteration, result.__next__)
        self.assertTrue(isfile(join(self.outDirectory, 'filename')))

    def testSecondAddWhenFirstIsSuspended(self):
        self.createMsgbox(asynchronous=True)
        myreactor = CallTrace('reactor')
        myreactor.returnValues['suspend'] = 'handle'

        result = self.msgbox.add('filename', 'data')
        suspend = next(result)
        suspend(myreactor, lambda: None)

        self.assertTrue('filename' in self.msgbox._suspended)
        newResult = self.msgbox.add('filename', 'data2')
        next(newResult)
        with open(join(self.msgbox._outDirectory, 'filename')) as fp:
            self.assertEqual('data', fp.read())
        self.assertTrue('filename' in self.msgbox._suspended)
        self.assertTrue(1, len(self.msgbox._waiting))

    def testAddAsynchronousYieldsSuspendAndReceivesAck(self):
        self.createMsgbox(asynchronous=True)
        myreactor = CallTrace('reactor')
        myreactor.returnValues['suspend'] = 'handle'

        result = self.msgbox.add('filename', 'data')

        self.assertFalse(isfile(join(self.outDirectory, 'filename')))
        suspend = next(result)
        suspend(myreactor, lambda: None)

        self.assertTrue(isfile(join(self.outDirectory, 'filename')))

        self.assertEqual(['suspend'], [m.name for m in myreactor.calledMethods])

        self.moveInRecord('filename.ack', '')
        self.assertTrue('filename' in self.msgbox._suspended)
        self.reactor.step()
        self.assertFalse('filename' in self.msgbox._suspended)

        self.assertEqual(['suspend'], [m.name for m in myreactor.calledMethods])

        self.assertRaises(StopIteration, result.__next__)

    def testAddTwoTimesAsynchronousYieldsSuspendAndReceivesAcks(self):
        self.createMsgbox(asynchronous=True)
        myreactor = CallTrace('reactor')
        myreactor.returnValues['suspend'] = 'handle'

        result = self.msgbox.add('filename', 'data')

        self.assertFalse(isfile(join(self.outDirectory, 'filename')))
        suspend = next(result)
        suspend(myreactor, lambda: None)

        result2 = self.msgbox.add('filename', 'data2')
        suspend2 = next(result2)
        suspend2(myreactor, lambda: None)

        with open(join(self.outDirectory, 'filename')) as fp:
            self.assertEqual('data', fp.read())

        self.assertEqual(['suspend', 'suspend'], [m.name for m in myreactor.calledMethods])

        remove(join(self.outDirectory, 'filename'))
        self.moveInRecord('filename.ack', '')
        self.assertTrue('filename' in self.msgbox._suspended)
        self.assertTrue(1, len(self.msgbox._waiting))
        self.reactor.step()
        next(result2)
        self.assertTrue('filename' in self.msgbox._suspended)
        self.assertFalse(0, len(self.msgbox._waiting))
        with open(join(self.outDirectory, 'filename')) as fp:
            self.assertEqual('data2', fp.read())

        self.moveInRecord('filename.ack', '')
        self.reactor.step()
        self.assertFalse('filename' in self.msgbox._suspended)

        self.assertEqual(['suspend', 'suspend'], [m.name for m in myreactor.calledMethods])

        self.assertRaises(StopIteration, result.__next__)
        self.assertRaises(StopIteration, result2.__next__)

    def testAddThreeTimesAsynchronousYieldsSuspendAndReceivesAcks(self):
        self.createMsgbox(asynchronous=True)
        myreactor = CallTrace('reactor')
        myreactor.returnValues['suspend'] = 'handle'

        result = self.msgbox.add('filename', 'data')

        self.assertFalse(isfile(join(self.outDirectory, 'filename')))
        suspend = next(result)
        suspend(myreactor, lambda: None)

        result2 = self.msgbox.add('filename', 'data2')
        suspend2 = next(result2)
        suspend2(myreactor, lambda: None)

        result3 = self.msgbox.add('filename', 'data3')
        suspend3 = next(result3)
        suspend3(myreactor, lambda: None)

        with open(join(self.outDirectory, 'filename')) as fp:
            self.assertEqual('data', fp.read())

        self.assertEqual(['suspend', 'suspend', 'suspend'], [m.name for m in myreactor.calledMethods])

        remove(join(self.outDirectory, 'filename'))
        self.moveInRecord('filename.ack', '')
        self.assertEqual(2, len(self.msgbox._waiting))
        self.reactor.step()
        next(result2)
        self.assertTrue('filename' in self.msgbox._suspended)
        self.assertEqual(1, len(self.msgbox._waiting))
        with  open(join(self.outDirectory, 'filename')) as fp:
            self.assertEqual('data2', fp.read())

        remove(join(self.outDirectory, 'filename'))
        self.moveInRecord('filename.ack', '')
        self.reactor.step()
        next(result3)
        self.assertTrue('filename' in self.msgbox._suspended)
        self.assertEqual(0, len(self.msgbox._waiting))
        with open(join(self.outDirectory, 'filename')) as fp:
            self.assertEqual('data3', fp.read())

        self.moveInRecord('filename.ack', '')
        self.reactor.step()
        self.assertFalse('filename' in self.msgbox._suspended)

        self.assertEqual(['suspend', 'suspend', 'suspend'], [m.name for m in myreactor.calledMethods])
        self.assertEqual([], self.msgbox._waiting)
        self.assertEqual({}, self.msgbox._suspended)

        self.assertRaises(StopIteration, result.__next__)
        self.assertRaises(StopIteration, result2.__next__)
        self.assertRaises(StopIteration, result3.__next__)

    def testAddAsynchronousYieldsSuspendAndReceivesError(self):
        self.createMsgbox(asynchronous=True)
        myreactor = CallTrace('reactor')
        myreactor.returnValues['suspend'] = 'handle'

        result = self.msgbox.add('filename', 'data')

        self.assertFalse(isfile(join(self.outDirectory, 'filename')))
        suspend = next(result)
        suspend(myreactor, lambda: None)

        self.assertTrue(isfile(join(self.outDirectory, 'filename')))

        self.assertEqual(['suspend'], [m.name for m in myreactor.calledMethods])

        self.moveInRecord('filename.error', 'Stacktrace')
        self.reactor.step()

        self.assertEqual(['suspend'], [m.name for m in myreactor.calledMethods])

        try:
            next(result)
            self.fail('Expected an exception.')
        except Exception as e:
            self.assertEqual("MsgboxRemoteError('Stacktrace',)", repr(e))
            from weightless.io import _suspend
            fileDict = {
                '__file__': ignoreLineNumbers.__code__.co_filename,
                '_suspend.py': _suspend.__file__,
                'msgbox.py': Msgbox.processFile.__code__.co_filename, 
            }
            self.assertEqualsWS(ignoreLineNumbers("""Traceback (most recent call last):
  File "%(__file__)s", line 442, in testAddAsynchronousYieldsSuspendAndReceivesError
    next(result)
  File "%(msgbox.py)s", line 167, in add
    suspend.getResult()
  File "%(_suspend.py)s", line [#], in getResult
    raise self._exception[1].with_traceback(self._exception[2])
  File "%(msgbox.py)s", line 124, in processFile
    raise MsgboxRemoteError(contents)
meresco.components.msgbox.msgbox.MsgboxRemoteError: Stacktrace""" % fileDict), ignoreLineNumbers(format_exc()))
        self.assertRaises(StopIteration, result.__next__)

    def testEscapeIdentifiersWhenUsedAsOutFilenames(self):
        msgbox = Msgbox(inDirectory=self.inDirectory, outDirectory=self.outDirectory)
        list(msgbox.add('.idwith.strange/char', 'data'))
        self.assertEqual(['%2Eidwith.strange%2Fchar'], self.listfiles(self.outDirectory))

    def testUnEscapeIdentifiersWhenUsedAsInFilenames(self):
        msgbox = Msgbox(inDirectory=self.inDirectory, outDirectory=self.outDirectory)
        interceptor = CallTrace(methods={'add': addMock})
        msgbox.addObserver(interceptor)
        open(join(self.inDirectory, '%2Eidwith.strange%2Fchar'), 'w').close()
        msgbox.processFile('%2Eidwith.strange%2Fchar')
        self.assertEqual('.idwith.strange/char', interceptor.calledMethods[0].kwargs['identifier'])

    def testUnEscapeIdentifiersForAck(self):
        msgbox = Msgbox(asynchronous=True, inDirectory=self.inDirectory, outDirectory=self.outDirectory)
        interceptor = CallTrace()
        interceptor.exceptions['add'] = Exception('hell!')
        msgbox.addObserver(interceptor)
        g = msgbox.add('.idwith.strange/char', 'data')
        suspend = next(g)
        suspend(CallTrace(), lambda: None)
        filename = '%2Eidwith.strange%2Fchar.ack'
        open(join(self.inDirectory, filename), 'w').close()
        msgbox.processFile(filename)
        suspend.getResult() # does not raise an Exception

    def testAckAndErrorAcceptedAfterSendDoesNotBlockForAck(self):
        self.createMsgbox()
        errorLog = []
        self.msgbox._logError = lambda error: errorLog.append(error)

        identifier = 'a:b:c'
        ''.join(self.msgbox.add(identifier, 'filedata'))
        self.assertTrue(isfile(join(self.outDirectory, identifier)))

        self.moveInRecord(identifier + '.ack', '')
        remove(join(self.outDirectory, identifier))
        self.reactor.step()
        self.assertEqual([], errorLog)

        self.assertEqual(1, len(self.observer.calledMethods))
        calledMethod = self.observer.calledMethods[0]
        self.assertEqual('add', calledMethod.name)
        self.assertEqual(identifier + '.ack', calledMethod.kwargs['identifier'])

        self.moveInRecord(identifier + '.error', 'Something bad happened.')
        self.reactor.step()
        self.assertEqual([], errorLog)

        self.assertEqual(2, len(self.observer.calledMethods))
        calledMethod = self.observer.calledMethods[1]
        self.assertEqual('add', calledMethod.name)
        self.assertEqual(identifier + '.error', calledMethod.kwargs['identifier'])

    def testOriginalFileRemovedBeforeAckAndNotAfter(self):
        self.createMsgbox()
        fileExistsOnAck = []
        def mockAck(filename):
            filepath = join(self.msgbox._inDirectory, filename)
            fileExistsOnAck.append(isfile(filepath))
            with open(filepath, 'w') as fp:
                fp.write(DATA)
        self.msgbox._ack = mockAck
        self.moveInRecord('aName')
        self.reactor.step()
        self.assertEqual([False], fileExistsOnAck)
        self.assertTrue(isfile(join(self.msgbox._inDirectory, 'aName')))

    def createMsgbox(self, asynchronous=False):
        self.msgbox = Msgbox(self.reactor, inDirectory=self.inDirectory, outDirectory=self.outDirectory, asynchronous=asynchronous)
        self.msgbox.addObserver(self.observer)
        self.msgbox.observer_init()

    def moveInRecord(self, filename, data=DATA):
        with open(join(self.tempdir, filename), 'w') as fp:
            fp.write(data)
        rename(join(self.tempdir, filename), join(self.inDirectory, filename))

    def listfiles(self, directory):
        return [f for f in listdir(directory) if isfile(join(directory, f))]

def ignoreLineNumbers(s):
    return sub("line \d+,", "line [#],", s)

