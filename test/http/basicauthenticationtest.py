## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from unittest import TestCase
from cq2utils import CallTrace
from meresco.components.http import BasicAuthentication
from base64 import b64encode
from weightless import compose

class BasicAuthenticationTest(TestCase):

    def testServerSendsChallenge(self):
        authentication = BasicAuthentication(realm='Test Realm')
        interceptor = CallTrace('httphandler', returnValues={'isValidLogin': True})
        authentication.addObserver(interceptor)
        response = ''.join(authentication.handleRequest(port='8080', RequestURI='/private', Method='GET'))
        self.assertTrue('WWW-Authenticate: Basic realm="Test Realm"\r\n' in response, response)

    def testHandleSimplePrivateRequest(self):
        authentication = BasicAuthentication(realm='Test Realm')
        interceptor = CallTrace('httphandler', returnValues={'isValidLogin': True, 'getUser':{'name':'aUser'}})
        authentication.addObserver(interceptor)
        headers = {'Authorization': 'Basic ' + b64encode('aUser:aPassword')}
        response = authentication.handleRequest(port='8080', RequestURI='/private', Method='GET', Headers=headers)
        list(compose(response))
        self.assertEquals('isValidLogin', interceptor.calledMethods[0].name)
        self.assertEquals(('aUser', 'aPassword'), interceptor.calledMethods[0].args)
        self.assertEquals('getUser', interceptor.calledMethods[1].name)
        self.assertEquals(('aUser',), interceptor.calledMethods[1].args)
        self.assertEquals('handleRequest', interceptor.calledMethods[2].name)
        self.assertEquals({'name': 'aUser'}, interceptor.calledMethods[2].kwargs['user'])

    def testHandleDifferentUsers(self):
        authentication = BasicAuthentication(realm='Test Realm')
        userdata = {'name':'aUser'}
        interceptor = CallTrace('httphandler', returnValues={'isValidLogin': True, 'getUser':userdata})
        authentication.addObserver(interceptor)
        headers = {'Authorization': 'Basic ' + b64encode('aUser:aPassword')}
        response = authentication.handleRequest(port='8080', RequestURI='/private', Method='GET', Headers=headers)
        list(compose(response))
        self.assertEquals({'name': 'aUser'}, interceptor.calledMethods[2].kwargs['user'])
        headers = {'Authorization': 'Basic ' + b64encode('anotherUser:anotherPassword')}
        userdata['name'] = 'anotherUser'
        response = authentication.handleRequest(port='8080', RequestURI='/private', Method='GET', Headers=headers)
        list(compose(response))
        self.assertEquals({'name': 'anotherUser'}, interceptor.calledMethods[5].kwargs['user'])

    def testDetectValidUserWithPasswordAndUserName(self):
        authentication = BasicAuthentication(realm='Test Realm')
        interceptor = CallTrace('httphandler', returnValues={'isValidLogin': True, 'handleRequest': (x for x in 'response')})
        authentication.addObserver(interceptor)
        headers = {'Authorization': 'Basic ' + b64encode('aUser:aPassword')}
        results = authentication.handleRequest(port='8080', RequestURI='/private', Method='GET', Headers=headers)
        response = ''.join(compose(results))
        self.assertFalse('WWW-Authenticate: Basic realm="Test Realm"\r\n' in response, response)
        interceptor.returnValues['isValidLogin'] = False
        headers = {'Authorization': 'Basic ' + b64encode('aUser:aCompletelyWrongPassword')}
        response = ''.join(authentication.handleRequest(port='8080', RequestURI='/private', Method='GET', Headers=headers))
        self.assertTrue('WWW-Authenticate: Basic realm="Test Realm"\r\n' in response, response)

    def testFailedLogin(self):
        authentication = BasicAuthentication(realm='Test Realm')
        interceptor = CallTrace('httphandler', returnValues={'isValidLogin': False})
        authentication.addObserver(interceptor)
        headers = {'Authorization': 'Basic ' + b64encode('aUser:aPassword')}
        response = ''.join(authentication.handleRequest(port='8080', RequestURI='/private', Method='GET', Headers=headers))
        self.assertEquals('isValidLogin', interceptor.calledMethods[0].name)
        self.assertTrue('WWW-Authenticate: Basic realm="Test Realm"\r\n' in response, response)
        self.assertTrue('Username or password are not valid.' in response)

    def testParseHeader(self):
        authentication = BasicAuthentication(realm='Test Realm')
        self.assertEquals(("username", "password"), authentication._parseHeader("Basic " + b64encode("username:password")))

    def testParseHeaderWeirdCases(self):
        authentication = BasicAuthentication(realm='Test Realm')
        self.assertEquals(None, authentication._parseHeader("bla bla bla"))
        self.assertEquals(None, authentication._parseHeader("NonsenseInPart0 QWxhZGRpbjpvcGVuIHNlc2FtZQ=="))
        self.assertEquals(None, authentication._parseHeader("Basic " + b64encode("nonsense")))

