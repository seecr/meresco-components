## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

from handlerequestfilter import HandleRequestFilter

class IpFilter(HandleRequestFilter):

    def __init__(self, name=None, allowedIps=None, allowedIpRanges=None):
        super(IpFilter, self).__init__(name=name, filterMethod=self._filter)
        self._allowedIps = allowedIps if allowedIps else []
        self._allowedIpRanges = [(self.convertToNumber(start), self.convertToNumber(end))
            for start,end in allowedIpRanges] if allowedIpRanges else []

    def _filter(self, Client, Headers, **kwargs):
        ipaddress = Client[0] if Client != None else '0.0.0.0'
        if 'X-Meresco-Ipfilter-Fake-Ip' in Headers and ipaddress == '127.0.0.1':
            ipaddress = Headers['X-Meresco-Ipfilter-Fake-Ip']
        return self.filterIpAddress(ipaddress)

    def filterIpAddress(self, ipaddress):
        if ipaddress in self._allowedIps:
            return True

        ipNumber = self.convertToNumber(ipaddress)
        for (start, end) in self._allowedIpRanges:
            if start <= ipNumber < end:
                return True

        return False

    def updateIps(self, ipAddresses=None, ipRanges=None):
        if ipAddresses is not None:
            self._allowedIps = ipAddresses
        if ipRanges is not None:
            self._allowedIpRanges = [(self.convertToNumber(start), self.convertToNumber(end))
                for start,end in ipRanges]

    @staticmethod
    def convertToNumber(ip):
        a,b,c,d = [int(x) for x in ip.split('.')]
        return pow(256,3)*a + pow(256,2)*b + pow(256, 1)*c + d

