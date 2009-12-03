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
from rfc822 import formatdate
from time import mktime, gmtime, timezone
from xml.sax.saxutils import escape as escapeXml
from os.path import dirname, abspath, join
from time import time

from merescocore.framework import Observable
from merescocore.components.http import utils as httputils, FileServer


javascriptDir = join(dirname(abspath(__file__)), 'js')

def _date(offset=0):
    return formatdate(mktime(gmtime()) - timezone + offset)

class Autocomplete(Observable):
    def __init__(self, path, inputs, maxresults, delay=100):
        Observable.__init__(self)
        self._path = path
        self._maxresults = maxresults
        self._delay = delay
        self._inputs = inputs
        self._fileServer = FileServer(documentRoot=javascriptDir)

    def handleRequest(self, arguments, path, **kwargs):
        filename = path.split('/')[-1]
        if filename in ['jquery.js', 'jquery.autocomplete.js']:
            yield self._javascript(filename, **kwargs)
        elif filename == 'autocomplete.js':
            yield self._autocompleteScript()
        else:
            yield self._prefixSearch(arguments)

    def _prefixSearch(self, arguments):
        t0 = time()
        yield httputils.okXml
        yield '<?xml version="1.0" encoding="utf-8"?><root>'
        for item, count in self.any.prefixSearch(
                fieldname=arguments['fieldname'][0],
                prefix=arguments['prefix'][0],
                maxresults=self._maxresults
            ):
            yield """<item count="%s">%s</item>""" % (count, escapeXml(item))
        yield '</root>'
        print "autocomplete -> prefixSearch", time()-t0

    def _javascript(self, filename, **kwargs):
        yield self._fileServer.handleRequest(path=filename, **kwargs)

    def _autocompleteScript(self):
        yield 'HTTP/1.0 200 OK' + httputils.CRLF
        yield 'Date: ' + _date() + httputils.CRLF
        yield 'Last-Modified: ' + _date() + httputils.CRLF
        yield 'Expires: ' + _date(60 * 60 * 24) + httputils.CRLF
        yield 'Content-Type: application/x-javascript' + httputils.CRLF

        yield httputils.CRLF
        yield """
            function buildSuggestionList(cont) {
                return function(obj) {
                            var res = [];
                            i = 0;
                            $(obj).find("item").each(function() {
                                i++;
                                res.push({
                                    id: i,
                                    value: $(this).text(),
                                    info: "(" + $(this).attr("count") + " results)"});
                            });

                            // will build suggestions list
                            cont(res);
                        }
            }
            """

        yield "$(document).ready(function() {"
        path = self._path
        delay = self._delay
        for inputId, fieldname in self._inputs:
            yield """
                $('#%(inputId)s').autocomplete({
                    ajax_get: function(key, cont) {
                                  $.get('%(path)s',
                                        {'prefix': key, 'fieldname': '%(fieldname)s'},
                                        buildSuggestionList(cont),
                                        'xml');},
                    minchars: 1,
                    cache: false,
                    delay: %(delay)s,
                    noresults: ""});

            """ % locals()
        yield "});"

