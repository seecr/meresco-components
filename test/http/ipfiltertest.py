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
# Copyright (C) 2012, 2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from seecr.test import CallTrace, SeecrTestCase
from meresco.core import Observable
from meresco.components.http import IpFilter

from weightless.core import compose, be

def handleRequest(*args, **kwargs):
    return
    yield

class IpFilterTest(SeecrTestCase):

    def assertValidIp(self,  address, ipranges=[], ips=[], headers={}):
        self._assertValidIp(address, ipranges, ips, headers, passed=True)

    def assertInvalidIp(self,  address, ipranges=[], ips=[], headers={}):
        self._assertValidIp(address, ipranges, ips, headers, passed=False)


    def _assertValidIp(self, address, ipranges, ips,headers, passed):
        self.observer = CallTrace('Observer', methods={'handleRequest': handleRequest})

        dna = be(
            (Observable(),
                (IpFilter(allowedIps=ips, allowedIpRanges=ipranges),
                    (self.observer, )
                )
            )
        )

        list(compose(dna.all.handleRequest(Client=(address,), Headers=headers)))
        if passed:
            self.assertEquals(1, len(self.observer.calledMethods))
            self.assertEquals('handleRequest', self.observer.calledMethods[0].name)
            self.assertEquals((address,), self.observer.calledMethods[0].kwargs['Client'])
        else:
            self.assertEquals(0, len(self.observer.calledMethods))

    def testIpfilterFakeIpHeaderForIntegrationTesting(self):
        self.assertInvalidIp('127.0.0.1', ips=['192.168.1.1'])
        self.assertInvalidIp('127.0.0.1', ips=['127.0.0.1'], headers={'X-Meresco-Ipfilter-Fake-Ip': '192.168.1.1'})
        self.assertValidIp('127.0.0.1', ips=['192.168.1.1'], headers={'X-Meresco-Ipfilter-Fake-Ip': '192.168.1.1'})
        self.assertInvalidIp('111.1.1.1', ips=['192.168.1.1'], headers={'X-Meresco-Ipfilter-Fake-Ip': '192.168.1.1'})
        
        self.assertValidIp('::1', ips=['2001:41c8:10:7b:aa:6:0:2'], headers={'X-Meresco-Ipfilter-Fake-Ip': '2001:41c8:10:7b:aa:6:0:2'})

    def testIpfilterFakeIpHeaderKwargsUnchanged(self):
        observer = CallTrace(methods={'handleRequest': handleRequest})
        ipf = IpFilter(allowedIps=['192.168.1.1'])

        dna = be(
            (Observable(),
                (ipf,
                    (observer,)
                )
            )
        )

        list(compose(dna.all.handleRequest(Client=('127.0.0.1',), Headers={'X-Meresco-Ipfilter-Fake-Ip': '192.168.1.1'})))

        self.assertEquals(1, len(observer.calledMethods))
        self.assertEquals((), observer.calledMethods[0].args)
        self.assertEquals({
            'Client': ('127.0.0.1',),
            'Headers': {'X-Meresco-Ipfilter-Fake-Ip': '192.168.1.1'}
        }, observer.calledMethods[0].kwargs)


    def testFilterSingleIp(self):
        self.assertValidIp('192.168.1.0', ips=["192.168.1.0"])
        self.assertInvalidIp('192.168.1.0', ips=["192.168.1.1"])
        self.assertInvalidIp('172.16.10.1', ips=["192.168.1.0"])
        self.assertValidIp('2001:41c8:10:7b:aa:6:0:2', ips=['2001:41c8:10:7b:aa:6:0:2'])

    def testZeroIPs(self):
        self.assertInvalidIp('0.0.0.0', ips=['192.168.1.1'])
        self.assertInvalidIp('0.0.0.0', ipranges=[('192.168.1.0', '192.168.1.255')])

    def testInRanges(self):
        self.assertValidIp('192.168.1.0', ipranges=[('192.168.1.0', '192.168.1.255')])
        self.assertValidIp('192.168.1.0', ipranges=['192.168.1.0/24'])
        self.assertValidIp('192.168.1.250', ipranges=['192.168.1.240/28'])
        self.assertValidIp('2001:41c8:10:7b:aa:6:0:2', ipranges=['2001:41c8:10:7b::/64'])
        self.assertValidIp('2001:41c8:10:7b:aa:6:0:2', ipranges=[('2001:41c8:10:7b:aa:6:0:1', '2001:41c8:10:7b:aa:6:0:5')])
        self.assertValidIp('192.168.1.128', ipranges=[('192.168.1.0', '192.168.1.255')])
        self.assertValidIp('192.168.1.128', ipranges=[('192.168.2.0', '192.168.2.255'), ('192.168.1.0', '192.168.1.255')])
        self.assertValidIp('192.168.1.255', ipranges=[('192.168.1.0', '192.168.1.255')])

    def testNotInRanges(self):
        self.assertInvalidIp('192.168.2.128', ipranges=[('192.168.1.0', '192.168.1.255')])
        self.assertInvalidIp('192.168.1.255', ipranges=[('192.168.1.0', '192.168.1.254')])
        self.assertInvalidIp('192.168.2.0', ipranges=[('192.168.1.0', '192.168.1.255')])
        self.assertInvalidIp('192.168.0.255', ipranges=[('192.168.1.0', '192.168.1.255')])
        self.assertInvalidIp('192.168.1.230', ipranges=['192.168.1.240/28'])
        self.assertInvalidIp('2001:41c8:10:7a:aa:6:0:2', ipranges=['2001:41c8:10:7b::/64'])

    def testFilterIpAddress(self):
        ipf = IpFilter(allowedIps=['10.0.0.1'])
        self.assertEquals(False, ipf.filterIpAddress(ipaddress='127.0.0.1'))
        self.assertEquals(True, ipf.filterIpAddress(ipaddress='10.0.0.1'))

        Headers = {'X-Meresco-Ipfilter-Fake-Ip': '10.99.99.99'}
        self.assertEquals(False, ipf.filterIpAddress(ipaddress='127.0.0.1', Headers=Headers))
        Headers = {'X-Meresco-Ipfilter-Fake-Ip': '10.0.0.1'}
        self.assertEquals(False, ipf.filterIpAddress(ipaddress='127.99.99.99', Headers=Headers))

        self.assertEquals(True, ipf.filterIpAddress(ipaddress='127.0.0.1', Headers=Headers))
        
        ipf = IpFilter(allowedIps=['2001:41c8:10:7b:aa:6:0:1'])
        self.assertEquals(False, ipf.filterIpAddress(ipaddress='::1'))
        self.assertEquals(True, ipf.filterIpAddress(ipaddress='2001:41c8:10:7b:aa:6:0:1'))


    def testUpdateIpFilter(self):
        observer = CallTrace(methods={'handleRequest': handleRequest})
        ipf = IpFilter(allowedIps=['192.168.1.1'], allowedIpRanges=[('10.0.0.1', '10.0.0.2'), '2001:41c8:10:7b::/64'])

        dna = be(
            (Observable(),
                (ipf,
                    (observer,)
                )
            )
        )

        list(compose(dna.all.handleRequest(Client=('127.0.0.1',), Headers={})))
        list(compose(dna.all.handleRequest(Client=('10.0.0.10',), Headers={})))
        self.assertEquals(0, len(observer.calledMethods))
        list(compose(dna.all.handleRequest(Client=('192.168.1.1',), Headers={})))
        self.assertEquals(1, len(observer.calledMethods))
        del observer.calledMethods[:]

        list(compose(dna.all.handleRequest(Client=('2001:41c8:10:7b:aa:6:0:2', ), Headers={})))
        self.assertEquals(1, len(observer.calledMethods))
        del observer.calledMethods[:]
        
        ipf.updateIps(ipAddresses=['127.0.0.1'], ipRanges=[('10.0.0.1', '10.0.0.255'), '2001:41c8:10:7c::/64'])
        list(compose(dna.all.handleRequest(Client=('192.168.1.1',), Headers={})))
        self.assertEquals(0, len(observer.calledMethods))
        list(compose(dna.all.handleRequest(Client=('127.0.0.1',), Headers={})))
        list(compose(dna.all.handleRequest(Client=('10.0.0.10',), Headers={})))
        self.assertEquals(2, len(observer.calledMethods))
        
        list(compose(dna.all.handleRequest(Client=('2001:41c8:10:7b:aa:6:0:2', ), Headers={})))
        self.assertEquals(2, len(observer.calledMethods))
        list(compose(dna.all.handleRequest(Client=('2001:41c8:10:7c:aa:6:0:2', ), Headers={})))
        self.assertEquals(3, len(observer.calledMethods))

