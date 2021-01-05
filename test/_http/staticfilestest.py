## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2016-2017, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2017, 2021 SURF https://www.surf.nl
# Copyright (C) 2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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
from meresco.components.http import StaticFiles, libdirForPrefix
from meresco.components.http.utils import parseResponse
from os.path import join
from os import makedirs
from weightless.core.utils import generatorToString

class StaticFilesTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        with open(join(self.tempdir, 'data.txt'), 'w') as f:
            f.write('DATA')
        self.sf = StaticFiles(libdir=self.tempdir, path='/jquery')

    def testPath(self):
        self.assertEqual('/jquery/', self.sf.path)

    def testData(self):
        headers, body = parseResponse(generatorToString(self.sf.handleRequest(path='/jquery/data.txt')))
        self.assertEqual('200', headers['StatusCode'])
        self.assertEqual('text/plain', headers['Headers']['Content-Type'])
        self.assertEqual('DATA', body)

    def testDoesNotExist(self):
        headers, body = parseResponse(generatorToString(self.sf.handleRequest(path='/jquery/no')))
        self.assertEqual('404', headers['StatusCode'])

    def testNotMyPath(self):
        self.assertEqual('', generatorToString(self.sf.handleRequest(path='/other')))

    def testIndex(self):
        sf = StaticFiles(libdir=self.tempdir, path='/path', allowDirectoryListing=True)
        headers, body = parseResponse(generatorToString(sf.handleRequest(path='/path/')))
        self.assertTrue('<a href="data.txt"' in body, body)

    def testPrefix(self):
        fullLibDir = join(self.tempdir, 'library-3.4.5')
        makedirs(fullLibDir)
        self.assertEqual(fullLibDir, libdirForPrefix(self.tempdir, 'library-3'))
        self.assertEqual(fullLibDir, libdirForPrefix(self.tempdir, 'libra'))
        self.assertRaises(ValueError, lambda: libdirForPrefix(self.tempdir, 'doesnotexist'))
        makedirs(join(self.tempdir, 'prefix-same-1'))
        makedirs(join(self.tempdir, 'prefix-same-2'))
        self.assertRaises(ValueError, lambda: libdirForPrefix(self.tempdir, 'prefix-same-'))

    def testPrefixStaticFiles(self):
        fullLibDir = join(self.tempdir, 'library-3.4.5')
        makedirs(fullLibDir)
        with open(join(fullLibDir, 'data.txt'), 'w') as f:
            f.write('DATA')
        prefixDir = join(self.tempdir, 'librar*')

        sf = StaticFiles(libdir=prefixDir, path='/jquery')

        headers, body = parseResponse(generatorToString(sf.handleRequest(path='/jquery/data.txt')))
        self.assertEqual('200', headers['StatusCode'])
        self.assertEqual('text/plain', headers['Headers']['Content-Type'])
        self.assertEqual('DATA', body)
