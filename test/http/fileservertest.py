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

from os.path import join
from shutil import rmtree
from tempfile import mkdtemp
from os import remove

from meresco.components.http.fileserver import FileServer

class FileServerTest(TestCase):

    def setUp(self):
        self.directory = mkdtemp()

    def tearDown(self):
        rmtree(self.directory)

    def testServeNoneExistingFile(self):
        fileServer = FileServer(self.directory)
        response = ''.join(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/doesNotExist", Method="GET", Headers={}))

        self.assertTrue("HTTP/1.0 404 Not Found" in response, response)
        self.assertTrue("<title>404 Not Found</title>" in response)

    def testFileExists(self):
        server = FileServer(self.directory)
        self.assertFalse(server.fileExists("/filename"))
        self.assertFalse(server.fileExists("/"))

        open(join(self.directory, 'filename'), "w").close()
        self.assertTrue(server.fileExists("/filename"))

        self.assertFalse(server.fileExists("//etc/shadow"))
        open('/tmp/testFileExists', 'w').close()
        try:
            self.assertFalse(server.fileExists("/tmp/testFileExists"))
            self.assertFalse(server.fileExists("//tmp/testFileExists"))
            self.assertFalse(server.fileExists("../testFileExists"))
        finally:
            remove('/tmp/testFileExists')

    def testServeFile(self):
        f = open(join(self.directory, 'someFile'), 'w')
        f.write("Some Contents")
        f.close()

        fileServer = FileServer(self.directory)
        response = ''.join(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/someFile", Method="GET", Headers={}))

        self.assertTrue("HTTP/1.0 200 OK" in response)
        self.assertTrue("Some Contents" in response)

    def testCacheControlStuff(self):
        f = open(join(self.directory, 'someFile'), 'w')
        f.write("Some Contents")
        f.close()

        fileServer = FileServer(self.directory)
        response = ''.join(fileServer.handleRequest(port=80, Client=('localhost', 9000), path="/someFile", Method="GET", Headers={}))

        self.assertTrue("Date: " in response)
        self.assertTrue("Last-Modified: " in response)
        self.assertTrue("Expires: " in response)
