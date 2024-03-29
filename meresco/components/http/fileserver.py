## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012-2013, 2015, 2017, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
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

from os.path import isfile, join, normpath, commonprefix, abspath, isdir, getsize
from email.utils import formatdate
from time import time
from stat import ST_MTIME, ST_SIZE
from os import stat, listdir

from meresco.components.http import utils as httputils
from meresco.components.http.utils import CRLF
from urllib.parse import unquote, unquote_plus
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
# XSD removed in Debian Bullsey package media-types (responsible for /etc/mime.types)
mimetypes.add_type("application/xml", ".xsd")


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
            'Content-Type': contentType,
            'Content-Length': getsize(self._filename),
        }

    def stream(self):
        yield bytes('HTTP/1.0 200 OK' + CRLF, encoding="utf-8")
        for item in self.getHeaders().items():
            yield bytes("%s: %s" % item + CRLF, encoding="utf-8")
        yield bytes(CRLF, encoding="utf-8")

        with open(self._filename, 'rb') as fp:
            data = fp.read(1024)
            while data:
                yield data
                data = fp.read(1024)

    def _date(self, offset=0):
        return formatdate(time() + offset)

class Directory(object):
    def __init__(self, path, documentRoot, basePath):
        self._path = path
        self._documentRoot = documentRoot
        self._basePath = basePath[:-1] if basePath.endswith('/') else basePath

    def getHeaders(self):
        return {}

    def _stripDocumentRoot(self, path):
        return '/' if path == self._documentRoot else path[len(self._documentRoot):]

    def stream(self):
        strippedPath = self._stripDocumentRoot(self._path)
        if strippedPath[-1] != "/":
            yield self._permanentRedirect(strippedPath)
            return

        yield bytes(httputils.Ok, encoding="utf-8")
        headers = {'Content-Type': httputils.ContentTypeHtml}
        headers.update(self.getHeaders())
        for item in headers.items():
            yield bytes("%s: %s" % item + CRLF, encoding="utf-8")
        yield bytes(CRLF, encoding="utf-8")
        totalPath = self._basePath + ('' if strippedPath.startswith('/') else '/') + strippedPath

        title = escapeHtml('Index of %(path)s' % dict(path=totalPath[:-1] or '/'))
        yield bytes("""<html>
    <head>
        <title>%(title)s</title>
    </head>
    <body>
        <h1>%(title)s</h1>
        <hr>
        <pre>
""" % locals(), encoding="utf-8")
        if strippedPath != '/':
            yield bytes('<a href="../">../</a>\n', encoding="utf-8")
        files = sorted(listdir(self._path))
        if len(files) > 0:
            longest = max(list(map(str.__len__, files))) + 2
            for filename in files:
                fullFilename = join(self._path, filename)
                fileStats = stat(fullFilename)
                if isdir(fullFilename):
                    filename += "/"
                yield bytes(
                '<a href=%s>%s</a>' % (quoteattr(filename), escapeHtml(filename)) +
                ' ' * (longest-len(filename)) +
                '%-20s' % formatdate(fileStats[ST_MTIME]) +
                '%20.d' % fileStats[ST_SIZE] +
                "\n", encoding="utf-8")
        yield bytes("""       </pre>
        <hr>
    </body>
</html>
        """, encoding="utf-8")
    def _permanentRedirect(self, path):
        yield bytes("HTTP/1.0 301 Moved Permanently\r\n", encoding="utf-8")
        yield bytes("Location: %s/\r\n\r\n" % path, encoding="utf-8")

class FileServer(object):
    def __init__(self, documentRoot, allowDirectoryListing=False, basePath=''):
        self._documentRoots = [abspath(d) for d in (documentRoot if type(documentRoot) is list else [documentRoot])]
        if not type(allowDirectoryListing) is bool:
            raise TypeError("allowDirectoryListing should be a boolean")
        self._allowDirectoryListing = allowDirectoryListing
        self._basePath = basePath

    def handleRequest(self, path, port=None, Client=None, Method=None, Headers=None, **kwargs):
        resolvedFileOrDir = self._findFile(path)
        if resolvedFileOrDir is None:
            yield bytes(
                httputils.notFoundHtml +
            '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n' +
            "<html><head>\n" +
            "<title>404 Not Found</title>\n" +
            "</head><body>\n" +
            "<h1>Not Found</h1>\n" +
            "<p>The requested URL %s was not found on this server.</p>\n" % path +
            "</body></html>\n", encoding="utf-8")
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
                return Directory(resolvedPath, documentRoot, basePath=self._basePath)

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

class SimpleServer(object):
    def __init__(self, completeHttpResponse):
        self._response = completeHttpResponse

    def handleRequest(self, *args, **kwargs):
        yield self._response

class StringServer(SimpleServer):
    def __init__(self, aString, contentType):
        SimpleServer.__init__(self, completeHttpResponse=CRLF.join([
            "HTTP/1.0 200 OK",
            "Content-Type: %s" % contentType,
            "",
            aString]))

