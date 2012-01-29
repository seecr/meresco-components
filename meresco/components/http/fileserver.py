## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os.path import isfile, join, normpath, commonprefix
from rfc822 import formatdate
from time import time
from stat import ST_MTIME
from os import stat

from meresco.components.http import utils as httputils
from meresco.components.http.utils import CRLF

import magic
magicCookie = magic.open(magic.MAGIC_MIME)
magicCookie.load()

import mimetypes
mimetypes.init()

class File(object):
    def __init__(self, filename):
        self._filename = filename

    def exists(self):
        return isfile(self._filename)

    def getHeaders(self, expires=3600):
        ext = self._filename.split(".")[-1]
        try:
            contentType = mimetypes.types_map["." + ext]
        except KeyError:
            contentType = "text/plain"

        return {
            'Date': self._date(),
            'Expires': self._date(expires),
            'Last-Modified': formatdate(stat(self._filename)[ST_MTIME]),
            'Content-Type': contentType
        }

    def stream(self):
        fp = open(self._filename)
        data = fp.read(1024)
        while data:
            yield data
            data = fp.read(1024)
        fp.close()

    def _date(self, offset=0):
        return formatdate(time() + offset)

class FileServer(object):
    def __init__(self, documentRoot):
        self._documentRoot = documentRoot

    def handleRequest(self, path, port=None, Client=None, Method=None, Headers=None, **kwargs):

        if not self.fileExists(path):
            yield httputils.notFoundHtml
            for line in ['<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">',
"<html><head>",
"<title>404 Not Found</title>",
"</head><body>",
"<h1>Not Found</h1>",
"<p>The requested URL %s was not found on this server.</p>" % path,
"<hr>",
"<address>Weightless Server at localhost Port 8080</address>",
"</body></html>"]:
                yield line
            raise StopIteration

        file = File(self._filenameFor(path))


        yield 'HTTP/1.0 200 OK' + CRLF
        for item in file.getHeaders().items():
            yield "%s: %s" % item + CRLF
        yield CRLF

        for part in file.stream():
            yield part

    def _filenameFor(self, filename):
        filename = '/'.join(part for part in filename.split('/') if part)
        path = normpath(join(self._documentRoot, filename))
        if commonprefix([self._documentRoot, path]) != self._documentRoot:
            raise ValueError('Filename "%s" not inside documentRoot.' % filename)
        return path

    def fileExists(self, filename):
        try:
            return isfile(self._filenameFor(filename))
        except ValueError:
            return False


class StringServer(object):
    def __init__(self, aString, contentType):
        self._aString = aString
        self._contentType = contentType

    def handleRequest(self, *args, **kwargs):
        yield 'HTTP/1.0 200 OK\r\n'
        yield "Content-Type: %s\r\n" % self._contentType
        yield "\r\n"

        yield self._aString
