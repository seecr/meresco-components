# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2006-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2006-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from seecr.test import SeecrTestCase, CallTrace

from os.path import join
from os import mkdir, listdir

from meresco.components.http import utils as httputils
from meresco.components.http.utils import CRLF, notFoundHtml

from meresco.components.log import LogFileServer, DirectoryLog

class LogFileServerTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        
        self.logDir = join(self.tempdir, 'log')
        directoryLog = DirectoryLog(self.logDir)
        self.qlfs = LogFileServer("Fancy <name>", directoryLog, basepath='/log')
    
    def testGenerateEmptyHtmlFileLinkListing(self):
        headers, body = "".join(self.qlfs.handleRequest(path="/log")).split(CRLF+CRLF)
        
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8', headers)
        self.assertTrue(body.startswith('<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n<html>'), body)
        self.assertTrue(body.rfind('</body>\n</html>') != -1, body)
        
        self.assertTrue('<title>"Fancy &lt;name&gt;" Logging</title>' in body, body)
        self.assertTrue('Logging - logfile listing' in body, body)
    
    def testEmptyDirectoryEmptyHtmlResult(self):
        headers, body = "".join(self.qlfs.handleRequest(path="/")).split(CRLF+CRLF)
        self.assertFalse('<li>' in body)
        
    def testDirectoryHtmlResult(self):
        filename = '2009-11-10-afile.1'
        open(join(self.logDir, filename), 'w').close()
        
        headers, body = "".join(self.qlfs.handleRequest(path="/log")).split(CRLF+CRLF)
        self.assertTrue('<li>' in body)
        self.assertTrue('<a href="/log/%s"' % filename in body, body)
        
        filename2 = '2009-11-22-yet_another_file.txt'
        open(join(self.logDir, filename2), 'w').close()
        headers, body = "".join(self.qlfs.handleRequest(path="/log/")).split(CRLF+CRLF)
        self.assertTrue('<a href="/log/%s"' % filename in body, body)
        self.assertTrue('<a href="/log/%s"' % filename2 in body, body)
        self.assertTrue(body.index(filename) > body.index(filename2), 'The files should be sorted.')
        
    def testPathNotSpecifiedAsIndexEffectivelyUsesMerescoFileServer(self):
        headers, body = "".join(self.qlfs.handleRequest(path="/thisIsWrongMister")).split(CRLF+CRLF)
        self.assertTrue("HTTP/1.0 404 Not Found" in headers, headers)
        
    def testPathIsASubDir(self):
        aSubDirCalled = "subdir"
        mkdir(join(self.logDir, aSubDirCalled))
        
        headers, body = "".join(self.qlfs.handleRequest(path="/%s" % aSubDirCalled)).split(CRLF+CRLF)
        
        self.assertTrue("HTTP/1.0 404 Not Found" in headers, headers)

    def testGetNonExistingLogFile(self):
        headers, body = "".join(self.qlfs.handleRequest(path="/log/thisIsWrongMister")).split(CRLF+CRLF)
        self.assertTrue("HTTP/1.0 404 Not Found" in headers, headers)
