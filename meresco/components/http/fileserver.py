## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from os.path import isfile, join
from rfc822 import formatdate
from time import mktime, gmtime, timezone
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
        return formatdate(mktime(gmtime()) - timezone + offset)

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
        while filename and filename[0] == '/':
            filename = filename[1:]
        filename = filename.replace('..', '')
        return join(self._documentRoot, filename)

    def fileExists(self, filename):
        return isfile(self._filenameFor(filename))


class StringServer(object):
    def __init__(self, aString, contentType):
        self._aString = aString
        self._contentType = contentType

    def handleRequest(self, *args, **kwargs):
        yield 'HTTP/1.0 200 OK\r\n'
        yield "Content-Type: %s\r\n" % self._contentType
        yield "\r\n"

        yield self._aString
