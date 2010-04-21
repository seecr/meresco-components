# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#    Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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

CRLF = "\r\n"
ContentTypeXml = "Content-Type: text/xml; charset=utf-8"
ContentTypeRss = "Content-Type: application/rss+xml"
ContentTypeHtml = "Content-Type: text/html; charset=utf-8"
ContentTypePlainText = "Content-Type: text/plain; charset=utf-8"

Ok = "HTTP/1.0 200 Ok" + CRLF

#200
okXml = "HTTP/1.0 200 OK" + CRLF + \
        ContentTypeXml + CRLF + \
        CRLF

okRss = "HTTP/1.0 200 OK" + CRLF + \
        ContentTypeRss + CRLF + \
        CRLF

okHtml = "HTTP/1.0 200 OK" + CRLF + \
        ContentTypeHtml + CRLF + \
        CRLF

okPlainText = "HTTP/1.0 200 OK" + CRLF + \
        ContentTypePlainText + CRLF + \
        CRLF

#403
forbiddenHtml = "HTTP/1.0 403 Forbidden" + CRLF + \
               ContentTypeHtml + CRLF + \
               CRLF

#404
notFoundHtml = "HTTP/1.0 404 Not Found" + CRLF + \
               ContentTypeHtml + CRLF + \
               CRLF

#500
serverErrorXml = "HTTP/1.0 500 Internal Server Error" + CRLF +\
                 ContentTypeXml + CRLF + \
                 CRLF

#503
serverUnavailableHtml = "HTTP/1.0 503 Service Unavailable" + CRLF +\
                        ContentTypeHtml + CRLF +\
                        CRLF 

def insertHeader(httpResponse, extraHeader):
    alreadyDone = False
    for response in httpResponse:
        if not alreadyDone and CRLF in response:
            alreadyDone = True
            statusLine, remainder = response.split(CRLF, 1)
            yield statusLine + CRLF
            yield extraHeader + CRLF
            if remainder != '':
                yield remainder
        else:
            yield response
