# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2008-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2008-2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from os.path import join, isfile
from os import makedirs, rename, listdir, remove
from meresco.components import lxmltostring

from meresco.components.inbox import Inbox, InboxException

class InboxTest(SeecrTestCase):

    def setUp(self):
        SeecrTestCase.setUp(self)
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
            (Transparent(),
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
            1/0

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

    def testFileDeletedBeforeHandling(self):
        identifier = 'repository:record'
        self.moveInRecord(identifier=identifier)
        self.removeRecord(identifier=identifier)

        self.reactor.step()
        errorFile = join(self.doneDirectory, '%s.record.error' % identifier)
        self.assertTrue(isfile(errorFile))

        errorMessage = open(errorFile).read()
        self.assertTrue(errorMessage.startswith("Traceback (most recent call last):"))
        self.assertTrue("IOError: [Errno 2] No such file or directory" in errorMessage, errorMessage)

    def testFileDeleteWhileProcessing(self):
        identifier = 'repository:record'

        def mockedAddCall(identifier=None, name=None, lxmlNode=None):
            identifierWithoutExtension = identifier[:-len('.record')]
            self.removeRecord(identifierWithoutExtension)
        self.observer.add = mockedAddCall

        self.moveInRecord(identifier=identifier)
        errorFile = join(self.doneDirectory, '%s.record.error' % identifier)
        self.assertFalse(isfile(errorFile))
        self.reactor.step()
        self.assertTrue(isfile(errorFile))

        errorMessage = open(errorFile).read()
        self.assertTrue(errorMessage.startswith("Traceback (most recent call last):"))
        self.assertTrue("rename(join(self._inboxDirectory, filename), join(self._doneDirectory, filename))" in errorMessage, errorMessage)
        self.assertTrue("OSError: [Errno 2] No such file or directory" in errorMessage, errorMessage)

    def moveInRecord(self, identifier, data="<record/>"):
        filename = join(self.tempdir, identifier+".record")
        open(filename, 'w').write(data)
        rename(filename, join(self.inboxDirectory, identifier+".record"))

    def removeRecord(self, identifier):
        remove(join(self.inboxDirectory, identifier+".record"))
