# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from weightless.core import Yield
import collections

CRLF = b"\r\n"
ContentTypeXml = b"text/xml; charset=utf-8"
ContentTypeRss = b"application/rss+xml"
ContentTypeHtml = b"text/html; charset=utf-8"
ContentTypePlainText = b"text/plain; charset=utf-8"
ContentTypeHeader = b"Content-Type: "

Ok = b"HTTP/1.0 200 OK" + CRLF

#200
okXml = Ok + \
        ContentTypeHeader + ContentTypeXml + CRLF + \
        CRLF

okRss = Ok + \
        ContentTypeHeader + ContentTypeRss + CRLF + \
        CRLF

okHtml = Ok + \
        ContentTypeHeader + ContentTypeHtml + CRLF + \
        CRLF

okPlainText = Ok + \
        ContentTypeHeader + ContentTypePlainText + CRLF + \
        CRLF

#204
successNoContentPlainText = b"HTTP/1.0 204 No Content" + CRLF +\
        ContentTypeHeader + ContentTypePlainText + CRLF + \
        CRLF

#302
redirectHttp = b"HTTP/1.0 302 Found" + CRLF + \
              b"Location: %s" + CRLF + \
              CRLF

#401
unauthorizedHtml = \
    b"HTTP/1.0 401 Unauthorized" + CRLF + \
    ContentTypeHeader + ContentTypeHtml + CRLF + \
    CRLF

#403
forbiddenHtml = b"HTTP/1.0 403 Forbidden" + CRLF + \
               ContentTypeHeader + ContentTypeHtml + CRLF + \
               CRLF

#404
notFoundHtml = b"HTTP/1.0 404 Not Found" + CRLF + \
               ContentTypeHeader + ContentTypeHtml + CRLF + \
               CRLF

#405
methodNotAllowedHtml = lambda allowed: b"HTTP/1.0 405 Method Not Allowed" + CRLF + \
               ContentTypeHeader + ContentTypeHtml + CRLF + \
               b"Allow: " + ', '.join(allowed) + CRLF + \
               CRLF

#500
serverErrorXml = b"HTTP/1.0 500 Internal Server Error" + CRLF +\
                 ContentTypeHeader + ContentTypeXml + CRLF + \
                 CRLF

serverErrorPlainText = b"HTTP/1.0 500 Internal Server Error" + CRLF +\
                 ContentTypeHeader + ContentTypePlainText + CRLF + \
                 CRLF

serverErrorHtml = b"HTTP/1.0 500 Internal Server Error" + CRLF +\
                  ContentTypeHeader + ContentTypeHtml + CRLF + \
                  CRLF
#503
serverUnavailableHtml = b"HTTP/1.0 503 Service Unavailable" + CRLF +\
                        ContentTypeHeader + ContentTypeHtml + CRLF +\
                        CRLF

def insertHeader(httpResponse, extraHeader):
    alreadyDone = False
    for response in httpResponse:
        if response is Yield or isinstance(response, collections.Callable):
            yield response
            continue

        if not alreadyDone and CRLF in response:
            alreadyDone = True
            statusLine, remainder = response.split(CRLF, 1)
            yield statusLine + CRLF
            yield extraHeader + CRLF
            if len(remainder) > 0:
                yield remainder
        else:
            yield response
