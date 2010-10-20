## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from handlerequestfilter import HandleRequestFilter

class IpFilter(HandleRequestFilter):

    def __init__(self, allowedIps=[], allowedIpRanges=[]):
        HandleRequestFilter.__init__(self, self._filter)
        self._allowedIps = allowedIps
        self._allowedIpRanges = [(self._convertToNumber(start), self._convertToNumber(end))
            for start,end in allowedIpRanges]

    def _filter(self, Client, Headers, **kwargs):
        ipaddress = Client[0] if Client != None else '0.0.0.0'
        if 'X-Meresco-Ipfilter-Fake-Ip' in Headers and ipaddress == '127.0.0.1':
            ipaddress = Headers['X-Meresco-Ipfilter-Fake-Ip']

        if ipaddress in self._allowedIps:
            return True

        ipNumber = self._convertToNumber(ipaddress)
        for (start, end) in self._allowedIpRanges:
            if start <= ipNumber < end:
                return True

        return False

    def _convertToNumber(self, ip):
        a,b,c,d = [int(x) for x in ip.split('.')]
        return pow(256,3)*a + pow(256,2)*b + pow(256, 1)*c + d

