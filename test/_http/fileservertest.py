## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
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

from os.path import join
from shutil import rmtree
from tempfile import mkdtemp
from os import remove, makedirs
from time import time
from email.utils import parsedate
from calendar import timegm
from io import BytesIO

from weightless.core import compose
from meresco.components.http.fileserver import FileServer
from seecr.test.utils import splitHttpHeaderBody

class FileServerTest(TestCase):
    def setUp(self):
        self.directory = mkdtemp()
        self.directory2 = mkdtemp()

    def tearDown(self):
        rmtree(self.directory)
        rmtree(self.directory2)

    def testInit(self):
        self.assertRaises(TypeError, lambda: FileServer())
        self.assertRaises(TypeError, lambda: FileServer(self.directory, self.directory2))
        FileServer(self.directory)
        FileServer(documentRoot=self.directory)
        FileServer(documentRoot=[self.directory, self.directory2])
        FileServer([self.directory, self.directory2])

    def testServeNotExistingFile(self):
        fileServer = FileServer(self.directory)
        response = ''.join(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/doesNotExist", Method="GET", Headers={}))
        self.assertTrue("HTTP/1.0 404 Not Found" in response, response)
        self.assertTrue("<title>404 Not Found</title>" in response)

    def testFindFile(self):
        server = FileServer([self.directory, self.directory2])
        self.assertFalse(server._findFile("/filename"))
        self.assertFalse(server._findFile("/"))

        open(join(self.directory, 'filename'), "w").close()
        open(join(self.directory2, 'filename2'), "w").close()
        open(join(self.directory, 'file with spaces'), 'w').close()
        self.assertTrue(server._findFile("/filename"))
        self.assertTrue(server._findFile("/filename2"))
        self.assertTrue(server._findFile("/file%20with%20spaces"))
        self.assertTrue(server._findFile("/file+with+spaces"))

        self.assertFalse(server._findFile("//etc/shadow"))
        open('/tmp/testFileExists', 'w').close()
        try:
            self.assertFalse(server._findFile("/tmp/testFileExists"))
            self.assertFalse(server._findFile("//tmp/testFileExists"))
            self.assertFalse(server._findFile("../testFileExists"))
        finally:
            remove('/tmp/testFileExists')

    def testServeFile(self):
        with open(join(self.directory, 'someFile'), 'w') as f:
            f.write("Some Contents")

        fileServer = FileServer(self.directory)
        header, body = splitHeaderBody(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/someFile", Method="GET", Headers={}))

        self.assertTrue("HTTP/1.0 200 OK" in header)
        self.assertTrue("Some Contents" in body)

    def testServeFileWithCorrectContentType(self):
        for extension, expectedType in [
                ('.js', 'application/javascript'),
                ('.xhtml', 'application/xhtml+xml'),
                ('.png', 'image/png'),
                ('.css', 'text/css')]:
            filename = 'someFile' + extension
            with open(join(self.directory, filename), 'w') as f:
                f.write("Some Contents")

            fileServer = FileServer(self.directory)
            header, body = splitHeaderBody(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/%s" % filename, Method="GET", Headers={}))
            headersList = header.split('\r\n')
            self.assertTrue("HTTP/1.0 200 OK" in header)
            self.assertTrue("Some Contents" in body)
            self.assertTrue('Content-Type: %s' % expectedType in headersList, headersList)

    def testFirstOneWins(self):
        with open(join(self.directory, 'someFile'), 'w') as f:
            f.write("Some Contents")
        with open(join(self.directory2, 'someFile'), 'w') as f:
            f.write("Different Contents")

        fileServer = FileServer(documentRoot=[self.directory, self.directory2])
        headers, body = splitHeaderBody(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/someFile", Method="GET", Headers={}))
        self.assertTrue("Some Contents" in body)
        self.assertFalse("Different Contents" in body)

        fileServer = FileServer(documentRoot=[self.directory2, self.directory])
        headers, body = splitHeaderBody(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/someFile", Method="GET", Headers={}))
        self.assertTrue("Different Contents" in body)
        self.assertFalse("Some Contents" in body)

    def testCacheControlStuff(self):
        with open(join(self.directory, 'someFile'), 'w') as fp:
            fp.write("Some Contents")

        fileServer = FileServer(self.directory)
        headers, body = splitHeaderBody(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/someFile", Method="GET", Headers={}))

        self.assertTrue("Date: " in headers)
        self.assertTrue("Last-Modified: " in headers)
        self.assertTrue("Expires: " in headers)

        headerValues = dict(tuple(a.strip() for a in line.split(':', 1)) for line in headers.split('\r\n') if ':' in line)
        date = timegm(parsedate(headerValues['Date']))
        expires = timegm(parsedate(headerValues['Expires']))
        self.assertTrue(1 > time() - date > 0, time() - date)
        self.assertTrue(61 * 60 > expires - date > 59 * 60, expires - date)

    def testPathShouldBeInDocumentRoot(self):
        documentRoot = join(self.directory, 'documentRoot')
        makedirs(documentRoot)
        notAllowedFile = join(self.directory, 'notAllowed.txt')
        with open(notAllowedFile, 'w') as fp:
            fp.write("DO NOT READ ME")
        fileServer = FileServer(documentRoot)

        response = ''.join(compose(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/../"+notAllowedFile, Method="GET", Headers={})))

        self.assertTrue("HTTP/1.0 404 Not Found" in response, response)
        self.assertTrue("<title>404 Not Found</title>" in response)

def splitHeaderBody(gen):
    response = BytesIO()
    for part in compose(gen):
        response.write(part.encode() if type(part) is str else part)
    return splitHttpHeaderBody(response.getvalue())
