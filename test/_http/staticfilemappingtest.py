## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2021 Seecr (Seek You Too B.V.) https://seecr.nl
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

from os.path import join
from weightless.core import asBytes
from weightless.io import Reactor

from meresco.components.http import StaticFileMapping
from meresco.components.http.utils import parseResponse

class StaticFileMappingTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        with open(join(self.tempdir, "x"), "w") as fp:
            fp.write("x"*100)

    def testGet(self):
        fm = StaticFileMapping(mapping={"/x": join(self.tempdir, "x")})

        headers, body = parseResponse(asBytes(fm.handleRequest(path="/x", Headers={})))
        self.assertEqual('200', headers['StatusCode'])
        self.assertEqual(100*b"x", body)

    def testETag(self):
        fm = StaticFileMapping(mapping={"/x": join(self.tempdir, "x")})

        headers, body = parseResponse(asBytes(fm.handleRequest(path="/x", Headers={})))
        self.assertTrue("Etag" in headers['Headers'], headers)
        etag = headers['Headers']['Etag']
        headers, body = parseResponse(asBytes(fm.handleRequest(path="/x", Headers={'etag': etag})))
        self.assertEqual('304', headers['StatusCode'])

    def testEtagUpdated(self):
        reactor = Reactor()

        fm = StaticFileMapping(mapping={"/x": join(self.tempdir, "x")}, reactor=reactor)
        headers, body = parseResponse(asBytes(fm.handleRequest(path="/x", Headers={})))
        self.assertTrue("Etag" in headers['Headers'], headers)
        etag = headers['Headers']['Etag']
        with open(join(self.tempdir, "x"), "w") as fp:
            fp.write("x"*200)
        reactor.step()
        headers, body = parseResponse(asBytes(fm.handleRequest(path="/x", Headers={})))
        self.assertTrue("Etag" in headers['Headers'], headers)
        self.assertNotEqual(headers['Headers']['Etag'], etag)

    def testPaths(self):
        fm = StaticFileMapping(mapping={"/x": join(self.tempdir, "x")})
        self.assertEqual(['/x'], fm.paths())
