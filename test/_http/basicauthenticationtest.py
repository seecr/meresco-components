## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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
from meresco.components.http import BasicAuthentication
from base64 import b64encode
from weightless.core import compose

def handleRequest(*args, **kwargs):
    return
    yield

class BasicAuthenticationTest(TestCase):

    def testServerSendsChallenge(self):
        authentication = BasicAuthentication(realm='Test Realm')
        interceptor = CallTrace('httphandler', returnValues={'isValidLogin': True}, methods={'handleRequest': handleRequest})
        authentication.addObserver(interceptor)
        response = ''.join(authentication.handleRequest(port='8080', RequestURI='/private', Method='GET'))
        self.assertTrue('WWW-Authenticate: Basic realm="Test Realm"\r\n' in response, response)

    def testHandleSimplePrivateRequest(self):
        authentication = BasicAuthentication(realm='Test Realm')
        interceptor = CallTrace('httphandler', returnValues={'isValidLogin': True, 'getUser':{'name':'aUser'}}, methods={'handleRequest': handleRequest})
        authentication.addObserver(interceptor)
        headers = {'Authorization': b'Basic ' + b64encode(b'aUser:aPassword')}
        response = authentication.handleRequest(port='8080', RequestURI='/private', Method='GET', Headers=headers)
        list(compose(response))
        self.assertEqual('isValidLogin', interceptor.calledMethods[0].name)
        self.assertEqual((b'aUser', b'aPassword'), interceptor.calledMethods[0].args)
        self.assertEqual('getUser', interceptor.calledMethods[1].name)
        self.assertEqual((b'aUser',), interceptor.calledMethods[1].args)
        self.assertEqual('handleRequest', interceptor.calledMethods[2].name)
        self.assertEqual({'name': 'aUser'}, interceptor.calledMethods[2].kwargs['user'])

    def testHandleDifferentUsers(self):
        authentication = BasicAuthentication(realm='Test Realm')
        userdata = {'name':'aUser'}
        interceptor = CallTrace('httphandler', returnValues={'isValidLogin': True, 'getUser':userdata}, methods={'handleRequest': handleRequest})
        authentication.addObserver(interceptor)
        headers = {'Authorization': b'Basic ' + b64encode(b'aUser:aPassword')}
        response = authentication.handleRequest(port='8080', RequestURI='/private', Method='GET', Headers=headers)
        list(compose(response))
        self.assertEqual({'name': 'aUser'}, interceptor.calledMethods[2].kwargs['user'])
        headers = {'Authorization': b'Basic ' + b64encode(b'anotherUser:anotherPassword')}
        userdata['name'] = 'anotherUser'
        response = authentication.handleRequest(port='8080', RequestURI='/private', Method='GET', Headers=headers)
        list(compose(response))
        self.assertEqual({'name': 'anotherUser'}, interceptor.calledMethods[5].kwargs['user'])

    def testDetectValidUserWithPasswordAndUserName(self):
        authentication = BasicAuthentication(realm='Test Realm')
        interceptor = CallTrace('httphandler', returnValues={'isValidLogin': True}, methods={'handleRequest': lambda *a, **kw: (x for x in 'response')})
        authentication.addObserver(interceptor)
        headers = {'Authorization': b'Basic ' + b64encode(b'aUser:aPassword')}
        results = authentication.handleRequest(port='8080', RequestURI='/private', Method='GET', Headers=headers)
        response = ''.join(compose(results))
        self.assertFalse('WWW-Authenticate: Basic realm="Test Realm"\r\n' in response, response)
        interceptor.returnValues['isValidLogin'] = False
        headers = {'Authorization': b'Basic ' + b64encode(b'aUser:aCompletelyWrongPassword')}
        response = ''.join(authentication.handleRequest(port='8080', RequestURI='/private', Method='GET', Headers=headers))
        self.assertTrue('WWW-Authenticate: Basic realm="Test Realm"\r\n' in response, response)

    def testFailedLogin(self):
        authentication = BasicAuthentication(realm='Test Realm')
        interceptor = CallTrace('httphandler', returnValues={'isValidLogin': False}, methods={'handleRequest': handleRequest})
        authentication.addObserver(interceptor)
        headers = {'Authorization': b'Basic ' + b64encode(b'aUser:aPassword')}
        response = ''.join(authentication.handleRequest(port='8080', RequestURI='/private', Method='GET', Headers=headers))
        self.assertEqual('isValidLogin', interceptor.calledMethods[0].name)
        self.assertTrue('WWW-Authenticate: Basic realm="Test Realm"\r\n' in response, response)
        self.assertTrue('Username or password are not valid.' in response)

    def testParseHeader(self):
        authentication = BasicAuthentication(realm='Test Realm')
        self.assertEqual((b"username", b"password"), authentication._parseHeader(b"Basic " + b64encode(b"username:password")))

    def testParseHeaderWeirdCases(self):
        authentication = BasicAuthentication(realm='Test Realm')
        self.assertEqual(None, authentication._parseHeader("bla bla bla"))
        self.assertEqual(None, authentication._parseHeader("NonsenseInPart0 QWxhZGRpbjpvcGVuIHNlc2FtZQ=="))
        self.assertEqual(None, authentication._parseHeader(b"Basic " + b64encode(b"nonsense")))

