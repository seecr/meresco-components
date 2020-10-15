# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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
        self.assertEqual(None, parseAbsoluteUrl('urn:iets'))
        self.assertEqual(None, parseAbsoluteUrl('example.org'))
        self.assertEqual(None, parseAbsoluteUrl('http://'))
        self.assertEqual(None, parseAbsoluteUrl('ï'))

    def testParseAbsoluteUrl(self):
        result = parseAbsoluteUrl('https://example.org')
        self.assertEqual({
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
        self.assertEqual({
                'host': 'example.org',
                'port': 8000,
                'path': '/sparql',
                'query': '',
                'fragment': '',
                'username': None,
                'password': None,
                'scheme': 'http',
            }, result)
        self.assertEqual(result.host, 'example.org')

        self.assertEqual({
                'username': 'user',
                'password': 'pass',
                'fragment': 'fragment',
                'host': 'example.org',
                'path': '/path',
                'query': '',
                'scheme': 'http',
                'port': 80,
            }, parseAbsoluteUrl('http://user:pass@example.org/path#fragment'))

        self.assertEqual({
                'username': 'user',
                'password': 'pass',
                'fragment': '',
                'host': 'example.org',
                'path': '/path',
                'query': '',
                'scheme': 'ftp',
                'port': 21,
            }, parseAbsoluteUrl('ftp://user:pass@example.org/path'))

        self.assertEqual({
                'username': None,
                'password': None,
                'fragment': '',
                'host': 'example.org',
                'path': '/',
                'query': '',
                'scheme': 'udp',
                'port': 1234
            }, parseAbsoluteUrl('udp://example.org:1234/'))


        self.assertEqual({
                'username': None,
                'password': None,
                'fragment': '',
                'host': 'example.org',
                'path': '/',
                'query': '',
                'scheme': 'unknown',
                'port': 80
            }, parseAbsoluteUrl('unknown://example.org/'))
