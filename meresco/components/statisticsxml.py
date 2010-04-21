# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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
from cgi import parse_qs
from urlparse import urlsplit

from time import mktime, gmtime

from meresco.components.statistics import AggregatorException
from weightless import compose
from xml.sax.saxutils import escape as xmlEscape

NAMESPACE="http://meresco.org/namespace/meresco/statistics"

class StatisticsXml(object):

    def __init__(self, statistics):
        self._statistics = statistics

    def handleRequest(self, RequestURI=None, *args, **kwargs):
        yield self._htmlHeader()
        yield '<statistics xmlns="%s"><header>%s' % (NAMESPACE, self._serverTime())
        arguments = self._parseArguments(RequestURI)

        try:
            fromTime = arguments.get("fromTime", None)
            if fromTime:
                yield "<fromTime>%s</fromTime>" % fromTime[0]
                fromTime = self._parseTime(fromTime[0])
            toTime = arguments.get("toTime", None)
            if toTime:
                yield "<toTime>%s</toTime>" % toTime[0]
                toTime = self._parseTime(toTime[0])
        except ValueError:
            yield "</header><error>Invalid Time Format. Times must be of the format 1970-01-01T00:00:00Z or any shorter subpart.</error></statistics>"
            raise StopIteration
        try:
            if "maxResults" in arguments:
                yield "<maxResults>%s</maxResults>" % arguments["maxResults"][0]
            maxResults = int(arguments.get("maxResults", [0])[0])
        except ValueError:
            yield "</header><error>maxResults must be number.</error></statistics>"
            raise StopIteration
        key = arguments.get("key", None)
        if not key:
            for stuff in self._listKeys():
                yield stuff
        else:
            key = tuple(key)
            yield compose(self._query(fromTime, toTime, key, maxResults))

    def _htmlHeader(self):
        return """HTTP/1.0 200 OK\r\nContent-Type: text/xml\r\n\r\n<?xml version="1.0" encoding="utf-8" ?>"""

    def _listKeys(self):
        yield "</header><availableKeys>"
        for keys in self._statistics.listKeys():
            yield "<key>"
            for key in keys:
                yield "<keyElement>%s</keyElement>" % key
            yield "</key>"
        yield "</availableKeys></statistics>"

    def _query(self, fromTime, toTime, key, maxResults):
        try:
            data = self._statistics.get(key, fromTime, toTime).items()
        except KeyError, e:
            yield "</header><error>Unknown key: %s</error></statistics>" % str(key)
            raise StopIteration
        except AggregatorException, e:
            yield "</header><error>Statistics Aggregation Exception: %s</error></statistics>" % str(e)
            raise StopIteration

        data = self._sorted(data)
        if maxResults:
            data = data[:maxResults]

        yield "<key>"
        yield self._list(key, "keyElement")
        yield "</key>"
        yield "</header>"
        yield "<observations>"
        for value, count in data:
            yield "<observation>"
            yield self._list(value, "value")
            yield "<occurrences>%s</occurrences>" % count
            yield "</observation>"
        yield "</observations></statistics>"

    def _sorted(self, data):
        def cmp((leftValue, leftCount), (rightValue, rightCount)):
            if not leftCount == rightCount:
                return rightCount - leftCount
            return rightValue > leftValue
        return sorted(data, cmp=cmp)

    def _list(self, list, tagName):
        if not list:
            yield "<%s>%s</%s>" % (tagName, "None", tagName)
        else:
            for e in list:
                yield "<%s>%s</%s>" % (tagName, xmlEscape(e), tagName)

    def _parseArguments(self, RequestURI):
        Scheme, Netloc, Path, Query, Fragment = urlsplit(RequestURI)
        arguments = parse_qs(Query)
        return arguments

    def _serverTime(self):
        return "<serverTime>%02d-%02d-%02dT%02d:%02d:%02dZ</serverTime>""" % gmtime()[:6]

    def _parseTime(self, s):
        result = []
        list = [(0, 4), (5, 7), (8, 10), (11, 13), (14, 16), (17, 19)]
        for (l, r) in list:
            if len(s) >= r:
                result.append((int(s[l:r])))
        return tuple(result)

