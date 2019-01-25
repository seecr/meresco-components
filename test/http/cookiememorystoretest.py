## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2016 Seecr (Seek You Too B.V.) http://seecr.nl
#
# This file is part of "Meresco Html"
#
# "Meresco Html" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Html" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Html"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import SeecrTestCase
from meresco.components.http import CookieMemoryStore
from time import sleep

class CookieMemoryStoreTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.d = CookieMemoryStore(name='name', timeout=0.1, httpOnly=False)
        self.d._now = lambda: 123456789.0

    def testCookieName(self):
        name = self.d.cookieName()
        self.assertTrue(name.startswith('name'))
        self.assertEquals(name, self.d.cookieName())
        self.assertNotEqual(name, CookieMemoryStore(timeout=0.1).cookieName())

    def testCreateCookie(self):
        result = self.d.createCookie('username')
        self.assertEquals('username', self.d.validateCookie(result['cookie'])['value'])
        self.assertNotEqual(result, self.d.createCookie('username'))
        self.assertEqual('Set-Cookie: {0}={1}; path=/; expires=Thu, 29 Nov 1973 21:33:09 GMT'.format(
            self.d.cookieName(), result['cookie']), result['header'])
        sleep(0.06)
        self.assertEquals('username', self.d.validateCookie(result['cookie'])['value'])
        sleep(0.06)
        self.assertEquals('username', self.d.validateCookie(result['cookie'])['value'])
        sleep(0.12)
        self.assertEquals(None, self.d.validateCookie(result['cookie']))

    def testCreateCookieSecure(self):
        d = CookieMemoryStore(name='name', timeout=0.1, secure=True, httpOnly=False)
        d._now = lambda: 123456789.0
        result = d.createCookie('username')
        self.assertEqual('Set-Cookie: {0}={1}; path=/; expires=Thu, 29 Nov 1973 21:33:09 GMT; Secure'.format(
            d.cookieName(), result['cookie']), result['header'])

    def testCreateCookieHttpOnly(self):
        d = CookieMemoryStore(name='name', timeout=0.1)
        d._now = lambda: 123456789.0
        result = d.createCookie('username')
        self.assertEqual('Set-Cookie: {0}={1}; path=/; expires=Thu, 29 Nov 1973 21:33:09 GMT; HttpOnly'.format(
            d.cookieName(), result['cookie']), result['header'])

        d = CookieMemoryStore(name='name', timeout=0.1, httpOnly=True)
        d._now = lambda: 123456789.0
        result = d.createCookie('username')
        self.assertEqual('Set-Cookie: {0}={1}; path=/; expires=Thu, 29 Nov 1973 21:33:09 GMT; HttpOnly'.format(
            d.cookieName(), result['cookie']), result['header'])
        
        d = CookieMemoryStore(name='name', timeout=0.1, httpOnly=False)
        d._now = lambda: 123456789.0
        result = d.createCookie('username')
        self.assertEqual('Set-Cookie: {0}={1}; path=/; expires=Thu, 29 Nov 1973 21:33:09 GMT'.format(
            d.cookieName(), result['cookie']), result['header'])

    def testCreateCookieForAnyObject(self):
        o = object()
        result = self.d.createCookie(o)
        self.assertEquals(o, self.d.validateCookie(result['cookie'])['value'])

    def testRemoveCookie(self):
        result = self.d.createCookie('username')
        self.assertEquals('username', self.d.validateCookie(result['cookie'])['value'])
        self.d.removeCookie(result['cookie'])
        self.assertEquals(None, self.d.validateCookie(result['cookie']))
        self.d.removeCookie(result['cookie'])

    def testRemoveCookiesWithObjectFilter(self):
        c1 = self.d.createCookie({'username': 'name'})
        c2 = self.d.createCookie(object())
        c3 = self.d.createCookie('otheruser')
        self.d.removeCookies(filter=lambda o:o.get('username') == 'name')
        self.assertFalse(self.d.validateCookie(c1['cookie']))
        self.assertTrue(self.d.validateCookie(c2['cookie']))
        self.assertTrue(self.d.validateCookie(c3['cookie']))
