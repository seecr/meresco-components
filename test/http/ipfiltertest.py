## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
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
from unittest import TestCase

from cq2utils import CallTrace
from meresco.core import be, Observable
from meresco.components.http import IpFilter

class IpFilterTest(TestCase):

    def assertValidIp(self,  address, ipranges=[], ips=[]):
        self._assertValidIp(address, ipranges, ips, passed=True)

    def assertInvalidIp(self,  address, ipranges=[], ips=[]):
        self._assertValidIp(address, ipranges, ips, passed=False)


    def _assertValidIp(self, address, ipranges, ips, passed):
        self.observer = CallTrace('Observer')

        dna = be(
            (Observable(),
                (IpFilter(allowedIps=ips, allowedIpRanges=ipranges),
                    (self.observer, )
                )
            )
        )

        list(dna.all.handleRequest(Client=(address,)))
        if passed:
            self.assertEquals(1, len(self.observer.calledMethods))
            self.assertEquals('handleRequest', self.observer.calledMethods[0].name)
            self.assertEquals((address,), self.observer.calledMethods[0].kwargs['Client'])
        else:
            self.assertEquals(0, len(self.observer.calledMethods))

    def testFilterSingleIp(self):
        self.assertValidIp('192.168.1.0', ips=["192.168.1.0"])
        self.assertInvalidIp('192.168.1.0', ips=["192.168.1.1"])
        self.assertInvalidIp('172.16.10.1', ips=["192.168.1.0"])

    def testZeroIPs(self):
        self.assertInvalidIp('0.0.0.0', ips=['192.168.1.1'])
        self.assertInvalidIp('0.0.0.0', ipranges=[('192.168.1.0', '192.168.1.255')])

    def testInRanges(self):
        self.assertValidIp('192.168.1.0', ipranges=[('192.168.1.0', '192.168.1.255')])
        self.assertValidIp('192.168.1.128', ipranges=[('192.168.1.0', '192.168.1.255')])
        self.assertValidIp('192.168.1.128', ipranges=[('192.168.2.0', '192.168.2.255'), ('192.168.1.0', '192.168.1.255')])

    def testNotInRanges(self):
        self.assertInvalidIp('192.168.2.128', ipranges=[('192.168.1.0', '192.168.1.255')])
        self.assertInvalidIp('192.168.1.255', ipranges=[('192.168.1.0', '192.168.1.255')])
        self.assertInvalidIp('192.168.2.0', ipranges=[('192.168.1.0', '192.168.1.255')])
        self.assertInvalidIp('192.168.0.255', ipranges=[('192.168.1.0', '192.168.1.255')])

    def testConvertToNumber(self):
        iprange = IpFilter()

        self.assertEquals(3232235776, iprange._convertToNumber('192.168.1.0'))
        self.assertEquals(0, iprange._convertToNumber('0.0.0.0'))