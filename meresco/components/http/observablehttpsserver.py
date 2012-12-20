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
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.core import Observable

from weightless.http import HttpsServer
from cgi import parse_qs
from urlparse import urlsplit
from StringIO import StringIO
from socket import gethostname

from observablehttpserver import ObservableHttpServer

class ObservableHttpsServer(ObservableHttpServer):
    def __init__(self, *args, **kwargs):
        self._keyfile = kwargs.pop('keyfile')
        self._certfile = kwargs.pop('certfile')
        ObservableHttpServer.__init__(self, *args, **kwargs)

    def startServer(self):
        """Starts server,

        When running a https server on port 443, this method should be called by the
        root user. In other cases it will be started when initializing all observers,
        see observer_init()
        """
        self._httpsserver = HttpsServer(
                reactor=self._reactor,
                port=self._port,
                generatorFactory=self._connect,
                timeout=self._timeout,
                prio=self._prio,
                sok=self._sok,
                keyfile=self._keyfile,
                certfile=self._certfile,
                maxConnections=self._maxConnections,
                errorHandler=self._error,
                compressResponse=self._compressResponse,
                bindAddress=self._bindAddress
            )
        self._httpsserver.listen()
        self._started = True

