## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from unittest import TestCase
from seecr.test import CallTrace
from meresco.components.http import ArgumentsInSession
from meresco.core import Observable
from weightless.core import compose

class ArgumentsInSessionTest(TestCase):
    def setUp(self):
        self.argsInSession = ArgumentsInSession()
        self.observer = CallTrace('Observer')
        self.argsInSession.addObserver(self.observer)
        
        
    def testAddOnlyOnce(self):
        sessions = []
        def handleRequest(session=None, *args, **kwargs):
            sessions.append(session)
            yield 'goodbye'
        self.observer.handleRequest = handleRequest

        session = {}
        list(compose(self.argsInSession.handleRequest(session=session, arguments={'aap': ["+'noot'"]})))
        self.assertEqual(['noot'], sessions[0]['aap'])
        self.assertEqual(session, sessions[0])
        
        list(compose(self.argsInSession.handleRequest(session=session, arguments={'aap': ["+'noot'"]})))
        self.assertEqual(sessions[0], sessions[1])
        self.assertEqual(['noot'], sessions[0]['aap'])

    def testParseAndSetSessionVars(self):
        arguments = {}
        def handleRequest(session=None, *args, **kwargs):
            arguments.update(session)
            yield 'goodbye'
        self.observer.handleRequest = handleRequest
        list(compose(self.argsInSession.handleRequest(session={}, arguments={'key': ["+('a simple tuple',)"]})))
        self.assertEqual(1, len(arguments))
        self.assertTrue('key' in arguments)
        self.assertEqual( [('a simple tuple',)], arguments['key'])

    def testParseAndSetAndRemoveSessionVars2(self):
        arguments = {}
        def handleRequest(session=None, *args, **kwargs):
            arguments.update(session)
            yield 'goodbye'
        self.observer.handleRequest = handleRequest
        session = {}
        list(compose(self.argsInSession.handleRequest(session=session, arguments={'aap': ["+'noot'"]})))
        self.assertEqual( ['noot'], arguments['aap'])
        list(compose(self.argsInSession.handleRequest(session=session, arguments={'aap': ["-'noot'"]})))
        self.assertEqual( [], arguments['aap'])

    def testDoNotEvalAnything(self):
        response = ''.join(compose(self.argsInSession.handleRequest(session={}, arguments={'key': ["+exit(0)"]})))
        self.assertEqual("HTTP/1.0 400 Bad Request\r\n\r\nname 'exit' is not defined", response)

    def testAddWithoutSignImpliesPlus(self):
        arguments = {}
        def handleRequest(session=None, *args, **kwargs):
            arguments.update(session)
            yield 'goodbye'
        self.observer.handleRequest = handleRequest
        session = {}
        list(compose(self.argsInSession.handleRequest(session=session, arguments={'aap': ["noot"]})))
        self.assertEqual( ['noot'], arguments['aap'])

