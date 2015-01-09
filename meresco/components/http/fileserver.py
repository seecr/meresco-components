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

from os.path import isfile, join, normpath, commonprefix, abspath
from email.utils import formatdate
from time import time
from stat import ST_MTIME
from os import stat

from meresco.components.http import utils as httputils
from meresco.components.http.utils import CRLF
from urllib.parse import unquote, unquote_plus

import magic
magicCookie = magic.open(magic.MAGIC_MIME)
magicCookie.load()

import mimetypes
mimetypes.init()
# Override defaults (for redhat systems)
mimetypes.add_type("application/javascript", ".js")

# Add types
mimetypes.add_type("application/xhtml+xml", ".xhtml")


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
        self._documentRoots = documentRoot
        if hasattr(documentRoot, 'endswith'):
            self._documentRoots = [documentRoot]
        self._documentRoots = [abspath(d) for d in self._documentRoots]

    def handleRequest(self, path, port=None, Client=None, Method=None, Headers=None, **kwargs):
        file = self._findFile(path)
        if file is None:
            yield httputils.notFoundHtml
            yield '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n'
            yield "<html><head>\n"
            yield "<title>404 Not Found</title>\n"
            yield "</head><body>\n"
            yield "<h1>Not Found</h1>\n"
            yield "<p>The requested URL %s was not found on this server.</p>\n" % path
            yield "</body></html>\n"
            return
        yield 'HTTP/1.0 200 OK' + CRLF
        for item in list(file.getHeaders().items()):
            yield "%s: %s" % item + CRLF
        yield CRLF
        yield file.stream()

    def _findFile(self, filename):
        possibleFilenames = unquoteFilename(filename)
        for filename in possibleFilenames:
            filename = '/'.join(part for part in filename.split('/') if part)
            for documentRoot in self._documentRoots:
                path = normpath(join(documentRoot, filename))
                if commonprefix([documentRoot, path]) == documentRoot and isfile(path):
                    return File(path)


def unquoteFilename(filename):
    result = [filename]
    for m in [unquote, unquote_plus]:
        unquoted = m(filename)
        if unquoted not in result:
            result.append(unquoted)
    return result

class StringServer(object):
    def __init__(self, aString, contentType):
        self._aString = aString
        self._contentType = contentType

    def handleRequest(self, *args, **kwargs):
        yield 'HTTP/1.0 200 OK\r\n'
        yield "Content-Type: %s\r\n" % self._contentType
        yield "\r\n"

        yield self._aString

