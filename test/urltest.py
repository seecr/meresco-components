# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase
from meresco.components.url import parseAbsoluteUrl

class UrlTest(SeecrTestCase):
    def testParseAbsoluteUrlNotAbsolute(self):
        self.assertEquals(None, parseAbsoluteUrl('urn:iets'))
        self.assertEquals(None, parseAbsoluteUrl('example.org'))
        self.assertEquals(None, parseAbsoluteUrl('http://'))
        self.assertEquals(None, parseAbsoluteUrl('ï'))

    def testParseAbsoluteUrl(self):
        result = parseAbsoluteUrl('https://example.org')
        self.assertEquals({
                'host': 'example.org',
                'port': 443,
                'path': '',
                'query': '',
                'fragment': '',
                'username': None,
                'password': None,
                'scheme': 'https',
            }, result)
        result = parseAbsoluteUrl('http://example.org:8000/sparql')
        self.assertEquals({
                'host': 'example.org',
                'port': 8000,
                'path': '/sparql',
                'query': '',
                'fragment': '',
                'username': None,
                'password': None,
                'scheme': 'http',
            }, result)
        self.assertEquals(result.host, 'example.org')

        self.assertEquals({
                'username': 'user',
                'password': 'pass',
                'fragment': 'fragment',
                'host': 'example.org',
                'path': '/path',
                'query': '',
                'scheme': 'http',
                'port': 80,
            }, parseAbsoluteUrl('http://user:pass@example.org/path#fragment'))

        self.assertEquals({
                'username': 'user',
                'password': 'pass',
                'fragment': '',
                'host': 'example.org',
                'path': '/path',
                'query': '',
                'scheme': 'ftp',
                'port': 21,
            }, parseAbsoluteUrl('ftp://user:pass@example.org/path'))

        self.assertEquals({
                'username': None,
                'password': None,
                'fragment': '',
                'host': 'example.org',
                'path': '/',
                'query': '',
                'scheme': 'udp',
                'port': 1234
            }, parseAbsoluteUrl('udp://example.org:1234/'))


        self.assertEquals({
                'username': None,
                'password': None,
                'fragment': '',
                'host': 'example.org',
                'path': '/',
                'query': '',
                'scheme': 'unknown',
                'port': 80
            }, parseAbsoluteUrl('unknown://example.org/'))
