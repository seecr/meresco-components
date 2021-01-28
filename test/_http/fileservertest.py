## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012-2013, 2016-2017, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2016, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2017, 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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
from seecr.test.utils import mkdir

from os.path import join
from os import remove, makedirs
from time import time
from email.utils import parsedate
from calendar import timegm

from weightless.core.utils import asList, generatorToString
from meresco.components.http.fileserver import FileServer


class FileServerTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.directory = mkdir(self.tempdir, "directory1")
        self.directory2 = mkdir(self.tempdir, "directory2")

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
        with open(join(self.directory, 'someFile'), 'wb') as f:
            f.write(b"Some Contents")

        fileServer = FileServer(self.directory)
        response = asList(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/someFile", Method="GET", Headers={}))

        self.assertTrue("HTTP/1.0 200 OK\r\n" in response)
        self.assertTrue("Content-Length: 13\r\n" in response, response)
        self.assertTrue(b"Some Contents" in response, response)

    def testServeFileWithCorrectContentType(self):
        for extension, expectedType in [
                ('.js', 'application/javascript'),
                ('.xhtml', 'application/xhtml+xml'),
                ('.png', 'image/png'),
                ('.css', 'text/css')]:
            filename = 'someFile' + extension
            f = open(join(self.directory, filename), 'w')
            f.write("Some Contents")
            f.close()

            fileServer = FileServer(self.directory)
            response = generatorToString(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/%s" % filename, Method="GET", Headers={}))
            headersList = response.split('\r\n\r\n', 1)[0].split('\r\n')

            self.assertTrue("HTTP/1.0 200 OK" in response)
            self.assertTrue("Some Contents" in response)
            self.assertTrue('Content-Type: %s' % expectedType in headersList, headersList)

    def testFirstOneWins(self):
        with open(join(self.directory, 'someFile'), 'w') as f:
            f.write("Some Contents")
        with open(join(self.directory2, 'someFile'), 'w') as f:
            f.write("Different Contents")

        fileServer = FileServer(documentRoot=[self.directory, self.directory2])
        response = generatorToString(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/someFile", Method="GET", Headers={}))
        self.assertTrue("Some Contents" in response)
        self.assertFalse("Different Contents" in response)

        fileServer = FileServer(documentRoot=[self.directory2, self.directory])
        response = generatorToString(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/someFile", Method="GET", Headers={}))
        self.assertTrue("Different Contents" in response)
        self.assertFalse("Some Contents" in response)

    def testCacheControlStuff(self):
        with open(join(self.directory, 'someFile'), 'w') as f:
            f.write("Some Contents")

        fileServer = FileServer(self.directory)
        response = generatorToString(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/someFile", Method="GET", Headers={}))
        headers, body = response.split("\r\n\r\n")

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
        with open(notAllowedFile, 'w') as f:
            f.write("DO NOT READ ME")
        fileServer = FileServer(documentRoot)

        response = generatorToString(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/../"+notAllowedFile, Method="GET", Headers={}))

        self.assertTrue("HTTP/1.0 404 Not Found" in response, response)
        self.assertTrue("<title>404 Not Found</title>" in response)


    def testListDirectory(self):
        fileServer = FileServer(self.directory)
        response = generatorToString(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/"))
        self.assertTrue(response.startswith("HTTP/1.0 404 Not Found"), response)

        fileServer = FileServer(self.directory, allowDirectoryListing=True)
        with open(join(self.directory, "dummy.txt"), "w") as f:
            f.write("Dummy")

        subdir = mkdir(self.directory, "subdir")
        with open(join(self.directory, subdir, 'The "real" <deal>.txt'), "w") as f:
            f.write("to test escaping")

        response = generatorToString(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/"))
        self.assertTrue(response.startswith("HTTP/1.0 200 OK"), response)
        self.assertTrue("<title>Index of /</title>" in response, response)

        links = [line for line in response.split("\n") if line.startswith("<a href")]
        self.assertEqual(2, len(links))

        self.assertTrue(links[0].startswith('<a href="dummy.txt">dummy.txt</a>'), links[0])
        self.assertTrue(links[0].endswith(' 5'), links[0])
        self.assertTrue(links[1].startswith('<a href="subdir/">subdir/</a>'), links[1])

        response = generatorToString(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/subdir"))
        self.assertTrue(response.startswith("HTTP/1.0 301 Moved Permanently"), response)

        response = generatorToString(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/subdir/"))
        self.assertTrue("<title>Index of /subdir</title>" in response, response)
        links = [line for line in response.split("\n") if line.startswith("<a href")]
        self.assertEqual('<a href="../">../</a>', links[0])
        self.assertTrue(links[1].startswith('''<a href='The "real" &lt;deal&gt;.txt'>The "real" &lt;deal&gt;.txt</a>'''), links[1])
        self.assertTrue(links[1].endswith(' 16'), links[1])

        subdir = mkdir(self.directory, "subdir2")
        response = generatorToString(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/subdir2/"))
        self.assertTrue("<title>Index of /subdir2</title>" in response, response)
        links = [line for line in response.split("\n") if line.startswith("<a href")]
        self.assertTrue(1, len(links))
        hrs = [line for line in response.split("\n") if line.strip() == "<hr>"]
        self.assertEqual(2, len(hrs))

        response = generatorToString(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/does_not_exist/"))
        self.assertTrue(response.startswith("HTTP/1.0 404 Not Found"), response)

    def testListDirectoryBasePath(self):
        fileServer = FileServer(self.directory, allowDirectoryListing=True, basePath='/webpath/')
        with open(join(self.directory, "dummy.txt"), "w") as f:
            f.write("Dummy")
        mkdir(self.directory, "subdir")

        response = generatorToString(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/"))
        self.assertTrue(response.startswith("HTTP/1.0 200 OK"), response)
        self.assertTrue("<title>Index of /webpath</title>" in response, response)

        links = [line for line in response.split("\n") if line.startswith("<a href")]
        self.assertEqual(2, len(links))

        self.assertTrue(links[0].startswith('<a href="dummy.txt">dummy.txt</a>'), links[0])
        self.assertTrue(links[0].endswith(' 5'), links[0])
        self.assertTrue(links[1].startswith('<a href="subdir/">subdir/</a>'), links[1])

