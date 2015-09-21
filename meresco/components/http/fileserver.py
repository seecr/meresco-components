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

from os.path import isfile, join, normpath, commonprefix, abspath, isdir, basename
from rfc822 import formatdate
from time import time
from stat import ST_MTIME, ST_SIZE
from os import stat, listdir

from meresco.components.http import utils as httputils
from meresco.components.http.utils import CRLF
from urllib import unquote, unquote_plus
#from cgi import escape as escapeHtml
from xml.sax.saxutils import quoteattr, escape as escapeHtml

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
        yield 'HTTP/1.0 200 OK' + CRLF
        for item in self.getHeaders().items():
            yield "%s: %s" % item + CRLF
        yield CRLF

        fp = open(self._filename)
        data = fp.read(1024)
        while data:
            yield data
            data = fp.read(1024)
        fp.close()

    def _date(self, offset=0):
        return formatdate(time() + offset)

class Directory(object):
    def __init__(self, path, documentRoot):
        self._path = path
        self._documentRoot = documentRoot

    def getHeaders(self):
        return {}

    def _stripDocumentRoot(self, path):
        return '/' if path == self._documentRoot else path[len(self._documentRoot):]

    def stream(self):
        strippedPath = self._stripDocumentRoot(self._path)
        if strippedPath[-1] != "/":
            yield self._permanentRedirect(strippedPath)
            return
        
        yield 'HTTP/1.0 200 OK' + CRLF
        for item in self.getHeaders().items():
            yield "%s: %s" % item + CRLF
        yield CRLF

        title = 'Index of %(path)s' % dict(path=strippedPath)
        yield """<html>
    <head>
        <title>%(title)s</title>
    </head>
    <body>
        <h1>%(title)s</h1>
        <hr>
        <pre>
<a href="../">../</a>
""" % locals()
        files = sorted(listdir(self._path))
        if len(files) > 0:
            longest = max(map(str.__len__, files)) + 2
            for filename in files:
                fullFilename = join(self._path, filename)
                fileStats = stat(fullFilename)
                if isdir(fullFilename):
                    filename += "/"
                yield '<a href=%s>%s</a>' % (quoteattr(filename), escapeHtml(filename))
                yield ' ' * (longest-len(filename))
                yield '%-20s' % formatdate(fileStats[ST_MTIME])
                yield '%20.d' % fileStats[ST_SIZE]
                yield "\n"
        yield """       </pre>
        <hr>
    </body>
</html>
        """
    def _permanentRedirect(self, path):
        yield "HTTP/1.0 301 Moved Permanently\r\n"
        yield "Location: %s/\r\n\r\n" % path

class FileServer(object):
    def __init__(self, documentRoot, allowDirectoryListing=False):
        self._documentRoots = [abspath(d) for d in (documentRoot if type(documentRoot) is list else [documentRoot])]
        if not type(allowDirectoryListing) is bool:
            raise TypeError("allowDirectoryListing should be a boolean")
        self._allowDirectoryListing = allowDirectoryListing

    def handleRequest(self, path, port=None, Client=None, Method=None, Headers=None, **kwargs):
        resolvedFileOrDir = self._findFile(path)
        if resolvedFileOrDir is None:
            yield httputils.notFoundHtml
            yield '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n'
            yield "<html><head>\n"
            yield "<title>404 Not Found</title>\n"
            yield "</head><body>\n"
            yield "<h1>Not Found</h1>\n"
            yield "<p>The requested URL %s was not found on this server.</p>\n" % path
            yield "</body></html>\n"
            return
        yield resolvedFileOrDir.stream()

    def _findFile(self, filename):
        resolvedPaths = list(self._resolvePaths(filename))
        files = [resolvedPath for (resolvedPath, _) in resolvedPaths if isfile(resolvedPath)]
        if len(files) > 0:
            return File(files[0])
        if self._allowDirectoryListing:
            dirs = [(resolvedPath, documentRoot) for (resolvedPath, documentRoot) in resolvedPaths if isdir(resolvedPath)]
            if len(dirs) > 0:
                resolvedPath, documentRoot = dirs[0]
                if filename[-1] == '/':
                    resolvedPath += "/"
                return Directory(resolvedPath, documentRoot) if len(dirs) > 0 else None

    def _resolvePaths(self, filename):
        possibleFilenames = unquoteFilename(filename)
        for filename in possibleFilenames:
            filename = '/'.join(part for part in filename.split('/') if part)
            for documentRoot in self._documentRoots:
                path = normpath(join(documentRoot, filename))
                if commonprefix([documentRoot, path]) == documentRoot:
                    yield (path, documentRoot) 


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

