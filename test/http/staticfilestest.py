## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2016 Seecr (Seek You Too B.V.) http://seecr.nl
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
from meresco.components.http import StaticFiles
from meresco.components.http.utils import parseResponse
from os.path import join
from weightless.core import asString

class StaticFilesTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        with open(join(self.tempdir, 'data.txt'), 'w') as f:
            f.write('DATA')
        self.sf = StaticFiles(libdir=self.tempdir, path='/jquery')

    def testPath(self):
        self.assertEqual('/jquery/', self.sf.path)

    def testData(self):
        headers, body = parseResponse(asString(self.sf.handleRequest(path='/jquery/data.txt')))
        self.assertEqual('200', headers['StatusCode'])
        self.assertEqual('text/plain', headers['Headers']['Content-Type'])
        self.assertEqual('DATA', body)

    def testDoesNotExist(self):
        headers, body = parseResponse(asString(self.sf.handleRequest(path='/jquery/no')))
        self.assertEqual('404', headers['StatusCode'])

    def testNotMyPath(self):
        self.assertEqual('', asString(self.sf.handleRequest(path='/other')))
