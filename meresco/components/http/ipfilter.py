## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2012, 2014, 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2016 SURFmarket https://surf.nl
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

from .handlerequestfilter import HandleRequestFilter
from netaddr import IPAddress, IPRange, IPNetwork
import os

class IpFilter(HandleRequestFilter):
    def __init__(self, name=None, allowedIps=None, allowedIpRanges=None):
        super(IpFilter, self).__init__(name=name, filterMethod=self._filter)
        self.updateIps(ipAddresses=allowedIps, ipRanges=allowedIpRanges)
        self._ipaddress = self._defaultIpaddress
        if os.environ.get('TESTMODE', '').upper() == 'TRUE':
            self._ipaddress = self._fakeIpaddress

    def _filter(self, Client, Headers, **kwargs):
        return self.filterIpAddress(Client[0] if Client != None else '0.0.0.0', Headers)

    def filterIpAddress(self, ipaddress, Headers=None):
        ipaddress = IPAddress(self._ipaddress(ipaddress, Headers))

        if ipaddress in self._allowedIps:
            return True

        for allowedRange in self._allowedIpRanges:
            if ipaddress in allowedRange:
                return True
        return False

    def _defaultIpaddress(self, ipaddress, Headers):
        return ipaddress

    def _fakeIpaddress(self, ipaddress, Headers):
        if Headers and 'X-Meresco-Ipfilter-Fake-Ip' in Headers and ipaddress in ['127.0.0.1', '::1']:
            return Headers['X-Meresco-Ipfilter-Fake-Ip']
        return ipaddress

    def updateIps(self, ipAddresses=None, ipRanges=None):
        self._allowedIps = set(IPAddress(allowedIp) for allowedIp in ipAddresses) if ipAddresses else set()
        self._allowedIpRanges = set(IPRange(*each) if type(each) is tuple else IPNetwork(each) for each in ipRanges) if ipRanges else set()
