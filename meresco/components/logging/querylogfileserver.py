# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2006-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2006-2011 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.components.http import utils as httputils
from meresco.components.http.utils import CRLF

from cgi import escape as _escapeHtml

def escapeHtml(aString):
    return _escapeHtml(aString).replace('"','&quot;')

class QueryLogFileServer(object):
    """Story 4-4: QueryLogger

    Serve the logs through http and show a filelisting when not
    requesting a specific path.
    """
    
    def __init__(self, log, basepath):
        self._indexPaths = ['', '/']
        self._basepath = basepath        
        self._log = log
    
    def handleRequest(self, path, **kwargs):
        if path in [self._basepath + p for p in self._indexPaths]:
            return self._generateIndex(path)
        elif path.startswith(self._basepath) and self._log.logExists(self._logNameFromPath(path)):
            return self._generateSingleLog(path)
        else:
            return (x for x in [httputils.notFoundHtml, "<html><body><h1>FILE NOT FOUND</h1></body></html>"])
    
    def _generateIndex(self, path):
        yield httputils.okHtml
        yield HTML_PAGE_TOP
        for log in sorted(self._log.listlogs(), reverse=True):
            yield '<li><a href="%s/%s">%s</a></li>' % (self._basepath, escapeHtml(log), escapeHtml(log))
        yield HTML_PAGE_BOTTOM

    def _generateSingleLog(self, path):
        yield httputils.okPlainText
        for line in self._log.getlog(self._logNameFromPath(path)):
            yield line
            
    def _logNameFromPath(self, path):
        return path.split('/')[-1]


HTML_PAGE_TOP = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html>
<head>
    <title>Edurep SMB Query Logging</title>
</head>
<body>
    <h1>Query Logging - logfile listing</h1>
    <ul>
"""

HTML_PAGE_BOTTOM = """    </ul>
</body>
</html>"""
