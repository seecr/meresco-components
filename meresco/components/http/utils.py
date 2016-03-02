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
# Copyright (C) 2012-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 SURF http://www.surf.nl
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


CRLF = "\r\n"
ContentTypeXml = "text/xml; charset=utf-8"
ContentTypeRss = "application/rss+xml; charset=utf-8"
ContentTypeHtml = "text/html; charset=utf-8"
ContentTypePlainText = "text/plain; charset=utf-8"
ContentTypeJson = "application/json"
ContentTypeHeader = "Content-Type: "

Ok = "HTTP/1.0 200 OK" + CRLF

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

okJson = Ok + \
    ContentTypeHeader + ContentTypeJson + CRLF + \
    CRLF

#204
successNoContentPlainText = "HTTP/1.0 204 No Content" + CRLF +\
    ContentTypeHeader + ContentTypePlainText + CRLF + \
    CRLF

#302
redirectHttp = "HTTP/1.0 302 Found" + CRLF + \
    "Location: %s" + CRLF + \
    CRLF

#400
badRequestHtml = \
    "HTTP/1.0 400 Bad Request" + CRLF + \
    ContentTypeHeader + ContentTypeHtml + CRLF + \
    CRLF

#401
unauthorizedHtml = \
    "HTTP/1.0 401 Unauthorized" + CRLF + \
    ContentTypeHeader + ContentTypeHtml + CRLF + \
    CRLF

#403
forbiddenHtml = "HTTP/1.0 403 Forbidden" + CRLF + \
    ContentTypeHeader + ContentTypeHtml + CRLF + \
    CRLF

#404
notFoundHtml = "HTTP/1.0 404 Not Found" + CRLF + \
    ContentTypeHeader + ContentTypeHtml + CRLF + \
    CRLF

#405
methodNotAllowedHtml = lambda allowed: "HTTP/1.0 405 Method Not Allowed" + CRLF + \
    ContentTypeHeader + ContentTypeHtml + CRLF + \
    "Allow: " + ', '.join(allowed) + CRLF + \
    CRLF

#500
serverErrorXml = "HTTP/1.0 500 Internal Server Error" + CRLF +\
    ContentTypeHeader + ContentTypeXml + CRLF + \
    CRLF

serverErrorPlainText = "HTTP/1.0 500 Internal Server Error" + CRLF +\
    ContentTypeHeader + ContentTypePlainText + CRLF + \
    CRLF

serverErrorHtml = "HTTP/1.0 500 Internal Server Error" + CRLF +\
    ContentTypeHeader + ContentTypeHtml + CRLF + \
    CRLF

#502
badGatewayHtml = "HTTP/1.0 502 Bad Gateway" + CRLF + \
    ContentTypeHeader + ContentTypeHtml + CRLF + \
    CRLF

#503
serverUnavailableHtml = "HTTP/1.0 503 Service Unavailable" + CRLF +\
    ContentTypeHeader + ContentTypeHtml + CRLF +\
    CRLF


def insertHeader(httpResponse, extraHeader):
    alreadyDone = False
    for response in httpResponse:
        if response is Yield or callable(response):
            yield response
            continue

        if not alreadyDone and CRLF in response:
            alreadyDone = True
            statusLine, remainder = response.split(CRLF, 1)
            yield statusLine + CRLF
            yield extraHeader + CRLF
            if remainder != '':
                yield remainder
        else:
            yield response

def createHttpHeaders(additionalHeaders=None, userAgent=None):
    headers = {} if additionalHeaders is None else dict(additionalHeaders)
    if userAgent is not None:
        headers['User-Agent'] = userAgent
    return ''.join('\r\n{0}: {1}'.format(k, v) for k, v in sorted(headers.items()))

def findCookies(Headers, name):
    return [cookie.split('=',1)[-1].strip() for cookie in Headers.get('Cookie','').split(';') if cookie.strip().startswith('{}='.format(name))]