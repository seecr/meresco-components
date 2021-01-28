# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012, 2014-2016, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2016 SURFmarket https://surf.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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
from .ipfilter import IpFilter
from .handlerequestfilter import HandleRequestFilter


class Deproxy(Observable):
    def __init__(self, deproxyForIps=None, deproxyForIpRanges=None, name=None):
        Observable.__init__(self, name=name)
        self._ipfilter = IpFilter(allowedIps=deproxyForIps, allowedIpRanges=deproxyForIpRanges)

    def handleRequest(self, Client, Headers, port=80, **kwargs):
        clientHost, clientPort = Client
        OriginalClient = None
        if self._ipfilter.filterIpAddress(ipaddress=clientHost, Headers=Headers):
            OriginalClient = clientHost, clientPort
            clientHost = _lastFromCommaSeparated(Headers.get("X-Forwarded-For", clientHost))
            host = _lastFromCommaSeparated(Headers.get("X-Forwarded-Host",  Headers.get('Host', '')))
            if host != '':
                Headers['Host'] = host
                port = int(host.partition(':')[2] or '80')
        yield self.all.handleRequest(Client=(clientHost, clientPort), Headers=Headers, port=port, OriginalClient=OriginalClient, **kwargs)

    def updateIps(self, ipAddresses=None, ipRanges=None):
        self._ipfilter.updateIps(ipAddresses=ipAddresses, ipRanges=ipRanges)

class OnlyDeproxied(HandleRequestFilter):
    def __init__(self, **kwargs):
        HandleRequestFilter.__init__(self, filterMethod=self._filter, **kwargs)

    def _filter(self, OriginalClient=None, **kwargs):
        return OriginalClient is not None

def _lastFromCommaSeparated(s):
    return ''.join([p.strip() for p in s.split(',') if p.strip()][-1:])
