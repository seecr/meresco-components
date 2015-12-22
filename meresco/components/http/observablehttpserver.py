# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012-2013, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from traceback import print_exc
from urlparse import parse_qs, urlsplit
from StringIO import StringIO

from weightless.core import compose
from weightless.http import HttpServer

from meresco.core import Observable

from utils import serverUnavailableHtml


class ObservableHttpServer(Observable):
    def __init__(self, reactor, port, timeout=1, prio=None, sok=None, maxConnections=None, compressResponse=True, bindAddress=None):
        Observable.__init__(self)
        self._port = port
        self._reactor = reactor
        self._timeout = timeout
        self._started = False
        self._prio = prio
        self._sok = sok
        self._maxConnections = maxConnections
        self._compressResponse = compressResponse
        self._bindAddress = bindAddress

    def startServer(self):
        """Starts server,

        When running a http server on port 80, this method should be called by the
        root user. In other cases it will be started when initializing all observers,
        see observer_init()
        """
        self._httpserver = HttpServer(
                self._reactor,
                self._port,
                self._connect,
                timeout=self._timeout,
                prio=self._prio,
                sok=self._sok,
                maxConnections=self._maxConnections,
                errorHandler=self._error,
                compressResponse=self._compressResponse,
                bindAddress=self._bindAddress
            )
        self._httpserver.listen()
        self._started = True

    def observer_init(self):
        if not self._started:
            self.startServer()

    def _connect(self, **kwargs):
        return compose(self.handleRequest(port=self._port, **kwargs))

    def _error(self, **kwargs):
        yield serverUnavailableHtml +\
        '<html><head></head><body><h1>Service Unavailable</h1></body></html>'
        self.do.logHttpError(**kwargs)

    def handleRequest(self, RequestURI=None, **kwargs):
        scheme, netloc, path, query, fragments = urlsplit(RequestURI)
        arguments = parse_qs(query, keep_blank_values=True)
        requestArguments = {
            'scheme': scheme, 'netloc': netloc, 'path': path, 'query': query, 'fragments': fragments,
            'arguments': arguments,
            'RequestURI': RequestURI}
        requestArguments.update(kwargs)
        try:
            yield self.all.handleRequest(**requestArguments)
        except (AssertionError, SystemExit, KeyboardInterrupt):
            raise
        except Exception:
            print_exc()
            raise

    def setMaxConnections(self, m):
        self._httpserver.setMaxConnections(m)
