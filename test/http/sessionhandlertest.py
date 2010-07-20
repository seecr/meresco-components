## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
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

from unittest import TestCase
from meresco.components.http import SessionHandler, utils
from meresco.components.http.sessionhandler import Session
from weightless import compose
from cq2utils import CallTrace
from time import time, sleep

#Cookies RFC 2109 http://www.ietf.org/rfc/rfc2109.txt
class SessionHandlerTest(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.handler = SessionHandler(secretSeed='SessionHandlerTest')
        self.observer = CallTrace('Observer')
        self.handler.addObserver(self.observer)

    def testCreateSession(self):
        called = []
        def handleRequest(*args, **kwargs):
            called.append({'args':args, 'kwargs':kwargs})
            yield  utils.okHtml
            yield '<ht'
            yield 'ml/>'
        self.observer.handleRequest = handleRequest
        result = ''.join(compose(self.handler.handleRequest(RequestURI='/path', Client=('127.0.0.1', 12345), Headers={'a':'b'})))

        self.assertEquals(1, len(called))
        session = called[0]['kwargs']['session']
        self.assertTrue(session)
        self.assertEquals({'a':'b'}, called[0]['kwargs']['Headers'])
        self.assertTrue(('127.0.0.1', 12345), called[0]['kwargs']['Client'])
        header, body = result.split(utils.CRLF*2,1)
        self.assertEquals('<html/>', body)
        self.assertTrue('Set-Cookie' in header, header)
        headerParts = header.split(utils.CRLF)
        self.assertEquals("HTTP/1.0 200 OK", headerParts[0])
        sessionCookie = [p for p in headerParts[1:] if 'Set-Cookie' in p][0]
        self.assertTrue(sessionCookie.startswith('Set-Cookie: session='))
        self.assertTrue(sessionCookie.endswith('; path=/'))
        self.assertEquals('Set-Cookie: session=%s; path=/' % session['id'], sessionCookie)

    def testCreateSessionWithName(self):
        self.handler = SessionHandler(secretSeed='SessionHandlerTest', nameSuffix='Mine')
        self.observer = CallTrace('Observer')
        self.handler.addObserver(self.observer)
        def handleRequest(*args, **kwargs):
            yield  utils.okHtml
            yield '<html/>'
        self.observer.handleRequest = handleRequest
        result = ''.join(compose(self.handler.handleRequest(RequestURI='/path', Client=('127.0.0.1', 12345))))
        header, body = result.split(utils.CRLF*2,1)
        self.assertTrue('Set-Cookie' in header, header)
        headerParts = header.split(utils.CRLF)
        self.assertEquals("HTTP/1.0 200 OK", headerParts[0])
        sessionCookie = [p for p in headerParts[1:] if 'Set-Cookie' in p][0]
        self.assertTrue(sessionCookie.startswith('Set-Cookie: sessionMine='), sessionCookie)

    def testRetrieveCookie(self):
        sessions = []
        def handleRequest(session=None, *args, **kwargs):
            sessions.append(session)
            yield  utils.okHtml + '<html/>'
        self.observer.handleRequest = handleRequest
        result = ''.join(compose(self.handler.handleRequest(RequestURI='/path', Client=('127.0.0.1', 12345), Headers={})))
        result = ''.join(compose(self.handler.handleRequest(RequestURI='/path', Client=('127.0.0.1', 12345), Headers={'Cookie': 'session=%s' % sessions[0]['id']})))
        self.assertEquals(sessions[0], sessions[1])
        self.assertEquals(id(sessions[0]),id(sessions[1]))

    def testInjectAnyCookie(self):
        sessions = []
        def handleRequest(session=None, *args, **kwargs):
            sessions.append(session)
            yield  utils.okHtml + '<html/>'
        self.observer.handleRequest = handleRequest
        result = ''.join(compose(self.handler.handleRequest(RequestURI='/path', Client=('127.0.0.1', 12345), Headers={'Cookie': 'session=%s' % 'injected_id'})))
        self.assertNotEqual('injected_id', sessions[0]['id'])

    def testSetSessionVarsWithLink(self):
        arguments = {}
        def handleRequest(session=None, *args, **kwargs):
            arguments.update(kwargs)
            yield session.setLink('setvalue', 'key', 'value1')
            yield session.unsetLink('unsetvalue', 'key', 'value2')
        self.observer.handleRequest = handleRequest
        result = ''.join(compose(self.handler.handleRequest(RequestURI='/path', Client=('127.0.0.1', 12345), Headers={})))
        self.assertEquals(  '<a href="?key=%2B%27value1%27">setvalue</a>' +
                            '<a href="?key=-%27value2%27">unsetvalue</a>', result)

    def testSimpleDataTypeArgumentsViaURL(self):
        def handleRequest(session=None, *args, **kwargs):
            yield session.setLink('linktitle', 'key', ('a simple tuple',))
        self.observer.handleRequest = handleRequest
        result = ''.join(compose(self.handler.handleRequest(RequestURI='/path', Client=('127.0.0.1', 12345), Headers={})))
        self.assertEquals("""<a href="?key=%2B%28%27a+simple+tuple%27%2C%29">linktitle</a>""", result)

    def testCustomSessionTimeout(self):
        HALF_AN_HOUR = 3600 / 2
        currentTime = 123456789
        sessions = []
        def handleRequest(session=None, *args, **kwargs):
            sessions.append(session)
            yield  utils.okHtml + '<html/>'
        handler = SessionHandler(secretSeed='SessionHandlerTest', timeout=HALF_AN_HOUR)
        handler._sessions._now = lambda: currentTime
        observer = CallTrace('Observer')
        observer.handleRequest = handleRequest
        handler.addObserver(observer)

        result = ''.join(compose(handler.handleRequest(RequestURI='/path', Client=('127.0.0.1', 12345))))
        firstSessionId = self.assertSessionCookie(result)
        handler._sessions._now = lambda: currentTime + HALF_AN_HOUR - 1
        result = ''.join(compose(handler.handleRequest(RequestURI='/path', Client=('127.0.0.1', 12345), Headers={'Cookie': 'session=%s' % firstSessionId})))
        sessionIdHalfAnHourMinusOne = self.assertSessionCookie(result)

        self.assertEquals(firstSessionId, sessionIdHalfAnHourMinusOne)

        handler._sessions._now = lambda: currentTime + HALF_AN_HOUR + 1
        result = ''.join(compose(handler.handleRequest(RequestURI='/path'    , Client=('127.0.0.1', 12345), Headers={'Cookie': 'session=%s' % firstSessionId})))
        sessionIdHalfAnHourPlusOne = self.assertSessionCookie(result)

        self.assertEquals(firstSessionId, sessionIdHalfAnHourPlusOne)

        handler._sessions._now = lambda: currentTime + (HALF_AN_HOUR * 2) + 2
        result = ''.join(compose(handler.handleRequest(RequestURI='/path'    , Client=('127.0.0.1', 12345), Headers={'Cookie': 'session=%s' % firstSessionId})))
        sessionIdJustExpired = self.assertSessionCookie(result)

        self.assertNotEqual(firstSessionId, sessionIdJustExpired)

    def assertSessionCookie(self, handleRequestOutput, nameSuffix=''):
        header, body = handleRequestOutput.split(utils.CRLF*2,1)
        headerParts = header.split(utils.CRLF)
        sessionCookie = [p for p in headerParts[1:] if 'Set-Cookie' in p][0]
        cookieStartStr = 'Set-Cookie: session%s=' % nameSuffix
        self.assertTrue(sessionCookie.startswith(cookieStartStr), sessionCookie)

        sessionId = sessionCookie[len(cookieStartStr):sessionCookie.find(';')]
        return sessionId if sessionId else self.fail('Cookie-header has no value', sessionCookie)

# Cookie bevat:
# - id (session)
# - time/date
# - expiration
# - IPAdress (Client)
# - MD5( bovenstaande + secret)
