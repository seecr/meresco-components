## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
#    Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
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

from __future__ import with_statement
from cq2utils import CQ2TestCase, CallTrace

from meresco.core import be, Transparant

from weightless import Reactor

from os.path import join, isfile, basename
from os import makedirs, rename, listdir, system, chmod, remove
from lxml.etree import tostring
from shutil import rmtree
from stat import S_IXUSR, S_IRUSR, S_IWUSR
from time import sleep

from threading import Thread

from meresco.components.msgbox import Msgbox
from meresco.components.msgbox.msgbox import File


DATA = "<record/>"

def failingAddMock(identifier=None, filedata=None):
    raise ValueError()

class MsgboxTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.reactor = Reactor()
        self.observer = CallTrace('Observer')
        self.inDirectory = join(self.tempdir, 'in')
        self.outDirectory = join(self.tempdir, 'out')
        makedirs(self.inDirectory)
        makedirs(self.outDirectory)

    def testCheckDirectoriesOnCreate(self):
        self.createMsgbox()
        try:
            Msgbox(CallTrace('Reactor'), inDirectory="/no_such_in", outDirectory="/tmp")
            self.fail()
        except ValueError, e:
            self.assertEquals("directory /no_such_in does not exist", str(e))

        try:
            Msgbox(CallTrace('Reactor'), inDirectory="/tmp", outDirectory="/no_such_out")
            self.fail()
        except ValueError, e:
            self.assertEquals("directory /no_such_out does not exist", str(e))

    def testMovedInFileTriggersThings(self):
        self.createMsgbox()
        filename = 'repository:some:identifier:1.record'
        self.moveInRecord(filename=filename)
        self.reactor.step()
        calledMethod = self.observer.calledMethods[0]
        self.assertEquals('add', calledMethod.name)
        self.assertEquals(filename, calledMethod.kwargs['identifier'])
        self.assertEquals(join(self.inDirectory, filename), calledMethod.kwargs['filedata'].name)

    def testAckWrittenToOutOnSuccessfulProcessing(self):
        self.createMsgbox()
        filename = 'repository:some:identifier:1.record'
        self.moveInRecord(filename=filename)
        self.assertEquals(0, len(self.observer.calledMethods))
        self.assertTrue(isfile(join(self.inDirectory, filename)))
        self.assertFalse(isfile(join(self.outDirectory, filename + '.ack')))
        self.reactor.step()
        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertFalse(isfile(join(self.inDirectory, filename)))
        self.assertTrue(isfile(join(self.outDirectory, filename + '.ack')))

    def testProcessRecordsOnCommand(self):
        self.moveInRecord(filename='repo:ident:1.record')
        self.moveInRecord(filename='repo:ident:2.record')
        self.msgbox = Msgbox(self.reactor, inDirectory=self.inDirectory, outDirectory=self.outDirectory)
        self.msgbox.addObserver(self.observer)
        self.assertEquals(set(['repo:ident:1.record', 'repo:ident:2.record']), set(self.listfiles(self.inDirectory)))
        self.msgbox.processInDirectory()
        self.assertEquals(set(['repo:ident:1.record.ack', 'repo:ident:2.record.ack']), set(self.listfiles(self.outDirectory)))

    def testProcessFileErrorHandling(self):
        self.observer.add = failingAddMock
        self.createMsgbox()
        self.msgbox._logError = lambda m: None

        filename = 'repository:some:identifier:1.record'
        self.moveInRecord(filename=filename)
        self.msgbox.processFile(filename)
        self.assertFalse(isfile(join(self.inDirectory, filename)))
        errorFile = join(self.outDirectory, filename + '.error')
        self.assertTrue(isfile(errorFile))
        errorMessage = open(errorFile).read()
        self.assertTrue(errorMessage.startswith("Traceback (most recent call last):"))
        self.assertTrue(errorMessage.endswith("ValueError\n"), errorMessage)

    def testErrorHandlingWithReactorStep(self):
        self.observer.add = failingAddMock
        self.createMsgbox()
        self.msgbox._logError = lambda m: None

        filename = 'repo:identifier:1.record'
        self.moveInRecord(filename=filename)
        self.reactor.step()
        self.assertFalse(isfile(join(self.inDirectory, filename)))
        errorFile = join(self.outDirectory, filename + '.error')
        self.assertTrue(isfile(errorFile))
        errorMessage = open(errorFile).read()
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

        self.assertEquals(0, len(self.observer.calledMethods))
        self.assertTrue(isfile(join(self.inDirectory, filename)))
        self.assertFalse(isfile(join(self.outDirectory, filename)))
        self.reactor.step()
        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertFalse(isfile(join(self.inDirectory, filename)))
        self.assertFalse(isfile(join(self.outDirectory, filename + '.ack')))

    def testErrorHandlingAsynchronousMsgbox(self):
        self.observer.add = failingAddMock
        self.createMsgbox(asynchronous=True)
        self.msgbox._logError = lambda m: None

        filename = 'repo:identifier:1.record'
        self.moveInRecord(filename=filename)
        self.assertTrue(isfile(join(self.inDirectory, filename)))
        self.reactor.step()
        self.assertFalse(isfile(join(self.inDirectory, filename)))
        errorFile = join(self.outDirectory, filename + '.error')
        self.assertTrue(isfile(errorFile))
        errorMessage = open(errorFile).read()
        self.assertTrue(errorMessage.startswith("Traceback (most recent call last):"))
        self.assertTrue(errorMessage.endswith("ValueError\n"), errorMessage)
        self.assertTrue(self.msgbox._watcher in self.reactor._readers)
    
    def testAck(self):
        self.createMsgbox(asynchronous=True)
        filename='repository:some:identifier:1.record'
        open(join(self.inDirectory, filename), 'w').write(DATA)
        self.assertFalse(isfile(join(self.outDirectory, filename + '.ack')))
        self.msgbox._ack(filename)
        self.assertTrue(isfile(join(self.inDirectory, filename)))
        self.assertTrue(isfile(join(self.outDirectory, filename + '.ack')))

    def testError(self):
        self.createMsgbox(asynchronous=True)
        filename='repository:some:identifier:1.record'
        errormessage = "an error occurred"
        errorfile = join(self.outDirectory, filename + '.error')
        open(join(self.inDirectory, filename), 'w').write(DATA)
        self.assertFalse(isfile(errorfile))
        self.msgbox._error(filename, errormessage)
        self.assertTrue(isfile(join(self.inDirectory, filename)))
        self.assertFalse(isfile(join(self.outDirectory, filename + '.ack')))
        self.assertEquals(errormessage, open(errorfile).read())

    def testNoFilesInTmpWhenStarting(self):
        filename = "testFile"
        tmpDirectory = join(self.outDirectory, 'tmp')
        makedirs(tmpDirectory)
        open(join(tmpDirectory, filename), 'w').close()
        self.createMsgbox()
        self.assertEquals(0, len(self.listfiles(self.msgbox._tmpDirectory)))
   
    def testAddWithFilenameAndFiledata(self):
        self.createMsgbox()
        filename = "testfile"
        filedata = DATA
        list(self.msgbox.add(filename, filedata))
        outFiles = self.listfiles(self.outDirectory)
        tmpFiles = self.listfiles(self.msgbox._tmpDirectory)
        self.assertEquals(1, len(outFiles))
        self.assertEquals(0, len(tmpFiles))
        self.assertEquals(filename, outFiles[0])
        with open(join(self.outDirectory, outFiles[0]), 'r') as f:
            self.assertEquals(filedata, f.read())

    def testAddWithFileLikeObject(self):
        self.createMsgbox()
        filename = "testfile"
        filepath = join(self.tempdir, filename)
        open(filepath, "w").write(DATA)
        list(self.msgbox.add(filename, File(filepath), ignoredKwarg="e.g. useful to have parsed lxmlNode included in combination with XmlXPath filtering"))
        outFiles = self.listfiles(self.outDirectory)
        self.assertEquals(filename, outFiles[0])
        with open(join(self.outDirectory, outFiles[0]), 'r') as f:
            self.assertEquals(DATA, f.read())

    def testAddWithOpenFile(self):
        self.createMsgbox()
        filename = "testfile"
        filepath = join(self.tempdir, filename)
        open(filepath, "w").write(DATA)
        list(self.msgbox.add(filename, open(filepath), ignoredKwarg="e.g. useful to have parsed lxmlNode included in combination with XmlXPath filtering"))
        outFiles = self.listfiles(self.outDirectory)
        self.assertEquals(basename(filepath), outFiles[0])
        with open(join(self.outDirectory, outFiles[0]), 'r') as f:
            self.assertEquals(DATA, f.read())

    def testDuplicateReplacesOriginal(self):
        self.createMsgbox()
        filename = "testfile"
        list(self.msgbox.add(filename, DATA))
        data2 = "<a>something</a>"
        list(self.msgbox.add(filename, data2))
        outFiles = self.listfiles(self.outDirectory)
        self.assertEquals([filename], outFiles)
        self.assertEquals(data2, open(join(self.outDirectory, filename)).read())

    def testExistingAckReplaced(self):
        self.createMsgbox()
        filename = 'repository:some:identifier:1.record'
        self.moveInRecord(filename=filename)
        self.msgbox.processFile(filename)
        self.moveInRecord(filename=filename)
        self.msgbox.processFile(filename)
        self.assertEquals(2, len(self.observer.calledMethods))
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
            self.assertEquals(0, len(tmpFiles))
        finally:
            chmod(self.outDirectory, S_IRUSR | S_IWUSR | S_IXUSR)

    def testIgnoreFailedRemoveWhenNoExistsFromIn(self):
        self.createMsgbox()
        try:
            self.msgbox.processFile("existed_but_being_replaced_with_newer_instance_by_other_process")
        except Exception, e:
            self.fail(e)
        self.assertTrue(isfile(join(self.outDirectory, "existed_but_being_replaced_with_newer_instance_by_other_process.ack")))

    def testRaiseErrorWhenOtherFailureThenNotExists(self):
        self.createMsgbox()
        try:
            self.msgbox.processFile(self.tempdir)
            self.fail("Remove a directory should raise an error and not being ignored.")
        except OSError:
            pass
    
    def testAddSynchronousIsEmptyGenerator(self):
        self.createMsgbox()

        result = self.msgbox.add('filename', 'data')
        
        self.assertFalse(isfile(join(self.outDirectory, 'filename')))
        self.assertRaises(StopIteration, result.next)
        self.assertTrue(isfile(join(self.outDirectory, 'filename')))

    def testSecondAddWhenFirstIsSuspended(self):
        self.createMsgbox(asynchronous=True)
        myreactor = CallTrace('reactor')
        myreactor.returnValues['suspend'] = 'handle'

        result = self.msgbox.add('filename', 'data')
        suspend = result.next()
        suspend(myreactor, lambda: None)

        self.assertRaises(ValueError, self.msgbox.add('filename', 'data').next)
        self.assertRaises(ValueError, result.next)
        self.assertFalse('filename' in self.msgbox._suspended)

    def testAddAsynchronousYieldsSuspendAndReceivesAck(self):
        self.createMsgbox(asynchronous=True)
        myreactor = CallTrace('reactor')
        myreactor.returnValues['suspend'] = 'handle'

        result = self.msgbox.add('filename', 'data')
        
        self.assertFalse(isfile(join(self.outDirectory, 'filename')))
        suspend = result.next()
        suspend(myreactor, lambda: None)

        self.assertTrue(isfile(join(self.outDirectory, 'filename')))

        self.assertEquals(['suspend'], [m.name for m in myreactor.calledMethods])
       
        self.moveInRecord('filename.ack', '')
        self.assertTrue('filename' in self.msgbox._suspended)
        self.reactor.step()
        self.assertFalse('filename' in self.msgbox._suspended)

        self.assertEquals(['suspend'], [m.name for m in myreactor.calledMethods])

        self.assertRaises(StopIteration, result.next)

    def testAddAsynchronousYieldsSuspendAndReceivesError(self):
        self.createMsgbox(asynchronous=True)
        myreactor = CallTrace('reactor')
        myreactor.returnValues['suspend'] = 'handle'

        result = self.msgbox.add('filename', 'data')
        
        self.assertFalse(isfile(join(self.outDirectory, 'filename')))
        suspend = result.next()
        suspend(myreactor, lambda: None)

        self.assertTrue(isfile(join(self.outDirectory, 'filename')))

        self.assertEquals(['suspend'], [m.name for m in myreactor.calledMethods])
       
        self.moveInRecord('filename.error', 'Stacktrace')
        self.reactor.step()

        self.assertEquals(['suspend'], [m.name for m in myreactor.calledMethods])

        try:
            result.next()
            self.fail('Expected an exception.')
        except Exception, e:
            self.assertEquals('Stacktrace', str(e))
        self.assertRaises(StopIteration, result.next)

    def testEscapeIdentifiersWhenUsedAsOutFilenames(self):
        msgbox = Msgbox(inDirectory=self.inDirectory, outDirectory=self.outDirectory)
        list(msgbox.add('.idwith.strange/char', 'data'))
        self.assertEquals(['%2Eidwith.strange%2Fchar'], self.listfiles(self.outDirectory))

    def testUnEscapeIdentifiersWhenUsedAsInFilenames(self):
        msgbox = Msgbox(inDirectory=self.inDirectory, outDirectory=self.outDirectory)
        interceptor = CallTrace()
        msgbox.addObserver(interceptor)
        open(join(self.inDirectory, '%2Eidwith.strange%2Fchar'), 'w').close()
        msgbox.processFile('%2Eidwith.strange%2Fchar')
        self.assertEquals('.idwith.strange/char', interceptor.calledMethods[0].kwargs['identifier'])

    def testUnEscapeIdentifiersForAck(self):
        msgbox = Msgbox(asynchronous=True, inDirectory=self.inDirectory, outDirectory=self.outDirectory)
        interceptor = CallTrace()
        interceptor.exceptions['add'] = Exception('hell!')
        msgbox.addObserver(interceptor)
        g = msgbox.add('.idwith.strange/char', 'data')
        suspend = g.next()
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
        self.assertEquals([], errorLog)

        self.assertEquals(1, len(self.observer.calledMethods))
        calledMethod = self.observer.calledMethods[0]
        self.assertEquals('add', calledMethod.name)
        self.assertEquals(identifier + '.ack', calledMethod.kwargs['identifier'])

        self.moveInRecord(identifier + '.error', 'Something bad happened.')
        self.reactor.step()
        self.assertEquals([], errorLog)

        self.assertEquals(2, len(self.observer.calledMethods))
        calledMethod = self.observer.calledMethods[1]
        self.assertEquals('add', calledMethod.name)
        self.assertEquals(identifier + '.error', calledMethod.kwargs['identifier'])

    def testOverwrittenInsertInProcessFile(self):
        self.createMsgbox()
        mockAddTrigger = []
        errorRaised = []
        ackCalled = []
        errorCalled = []
        def mockAdd(*args, **kwargs):
            mockAddTrigger.append(1)
            while len(mockAddTrigger) < 2:
                sleep(0.01)
            # Will crash the 2nd time ...
            try:
                open(join(self.inDirectory, filename)).close()
            except:
                errorRaised.append(1)
                raise
        def mockAck(*args, **kwargs):
            ackCalled.append(1)
        def mockError(*args, **kwargs):
            errorCalled.append(1)
        self.observer.methods["add"] = mockAdd
        self.msgbox._error = mockError
        self.msgbox._ack = mockAck
        filename = 'dejavu.txt'
        filedata = "something"
        
        reactorThread = Thread(None, self.doubleStepper, "reactor")
        reactorThread.start()
        
        # Move in first record, wait until in add call (mockAdd)
        self.moveInRecord(filename)
        while len(mockAddTrigger) < 1:
            sleep(0.01)
        self.moveInRecord(filename)
        # Moved in second file, first step can continue (That step may not remove the input file, because it's overwritten by the second move in)
        mockAddTrigger.append(2)
        reactorThread.join()
        self.assertEquals(1, len(errorRaised))
        self.assertEquals(1, len(ackCalled))
        self.assertEquals(1, len(errorCalled))

    # helper methods
    def doubleStepper(self):
        self.reactor.step()
        self.reactor.step()

    def createMsgbox(self, asynchronous=False):
        self.msgbox = Msgbox(self.reactor, inDirectory=self.inDirectory, outDirectory=self.outDirectory, asynchronous=asynchronous)
        self.msgbox.addObserver(self.observer)
        self.msgbox.observer_init()

    def moveInRecord(self, filename, data=DATA):
        open(join(self.tempdir, filename), 'w').write(data)
        rename(join(self.tempdir, filename), join(self.inDirectory, filename))

    def listfiles(self, directory):
        return [f for f in listdir(directory) if isfile(join(directory, f))]
         
