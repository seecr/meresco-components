# -*- coding: utf-8 -*-
from cq2utils import CQ2TestCase, CallTrace

from merescocore.framework import be, Transparant

from weightless import Reactor

from os.path import join, isfile
from os import makedirs, rename, listdir
from lxml.etree import tostring

from merescocomponents.inbox import Inbox, InboxException

class InboxTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.reactor = Reactor()
        self.observer = CallTrace('Observer')
        self.inboxDirectory = join(self.tempdir, 'inbox')
        self.doneDirectory = join(self.tempdir, 'done')
        makedirs(self.inboxDirectory)
        makedirs(self.doneDirectory)
        self.inbox = Inbox(self.reactor, inboxDirectory=self.inboxDirectory, doneDirectory=self.doneDirectory)
        self.inbox.addObserver(self.observer)

    def testCheckDirectoriesOnCreate(self):
        try:
            Inbox(CallTrace('Reactor'), inboxDirectory="/no_such_inbox", doneDirectory="/tmp")
            self.fail()
        except InboxException, e:
            self.assertEquals("directory /no_such_inbox does not exist", str(e))

        try:
            Inbox(CallTrace('Reactor'), inboxDirectory="/tmp", doneDirectory="/no_such_done")
            self.fail()
        except InboxException, e:
            self.assertEquals("directory /no_such_done does not exist", str(e))

    def testMovedInFileTriggersThings(self):
        events = []
        self.inbox.processFile = lambda event: events.append(event)

        self.moveInRecord('repository:some:identifier:1')
        self.reactor.step()
        self.assertEquals(1, len(events))
        self.assertEquals("repository:some:identifier:1.record", events[0])


    def testProcessedGetsMovedToDone(self):
        self.moveInRecord(identifier='repository:some:identifier:1')

        self.assertEquals(0, len(self.observer.calledMethods))
        self.assertTrue(isfile(join(self.inboxDirectory, 'repository:some:identifier:1.record')))
        self.assertFalse(isfile(join(self.doneDirectory, 'repository:some:identifier:1.record')))
        self.reactor.step()
        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertFalse(isfile(join(self.inboxDirectory, 'repository:some:identifier:1.record')))
        self.assertTrue(isfile(join(self.doneDirectory, 'repository:some:identifier:1.record')))

    def testProcessRecordsOnCommand(self):
        self.inboxDirectory = join(self.tempdir, 'inbox2')
        self.doneDirectory = join(self.tempdir, 'done2')
        makedirs(self.inboxDirectory)
        makedirs(self.doneDirectory)

        self.moveInRecord(identifier='repo:ident:1')
        self.moveInRecord(identifier='repo:ident:2')
        self.moveInRecord(identifier='repo:ident:3')
        inbox = Inbox(self.reactor, inboxDirectory=self.inboxDirectory, doneDirectory=self.doneDirectory)
        dna = be(
            (Transparant(),
                (inbox,)
            )
        )
        dna.once.observer_init()
        self.assertEquals(set(['repo:ident:1.record', 'repo:ident:2.record', 'repo:ident:3.record']), set(listdir(self.inboxDirectory)))

        inbox.processInboxDirectory()

        self.assertEquals(set(['repo:ident:1.record', 'repo:ident:2.record', 'repo:ident:3.record']), set(listdir(self.doneDirectory)))


    def testErrorHandling(self):
        self.moveInRecord(identifier='repo:identifier:1')

        def mockedAddCall(identifier=None, name=None, lxmlNode=None):
            result = 1/0

        self.observer.add = mockedAddCall

        self.reactor.step()
        self.assertFalse(isfile(join(self.inboxDirectory, 'repo:identifier:1.record')))
        self.assertTrue(isfile(join(self.doneDirectory, 'repo:identifier:1.record')))
        errorFile = join(self.doneDirectory, 'repo:identifier:1.record.error')
        self.assertTrue(isfile(errorFile))

        errorMessage = open(errorFile).read()
        self.assertTrue(errorMessage.startswith("Traceback (most recent call last):"))
        self.assertTrue(errorMessage.endswith("ZeroDivisionError: integer division or modulo by zero\n"), errorMessage)

    def testNoXmlFile(self):
        identifier = 'repository:record'
        self.moveInRecord(identifier=identifier, data='this is no xml')
        self.reactor.step()
        errorFile = join(self.doneDirectory, identifier+'.record.error')
        self.assertTrue(isfile(errorFile))
        self.assertFalse(isfile(join(self.inboxDirectory, identifier+'.record')))
        self.assertTrue('Start tag expected' in open(errorFile).read())

    def moveInRecord(self, identifier, data="<record/>"):
        filename = join(self.tempdir, identifier+".record")
        open(filename, 'w').write(data)
        rename(filename, join(self.inboxDirectory, identifier+".record"))
