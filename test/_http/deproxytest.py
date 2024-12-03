# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012, 2014-2016, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
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

from unittest import TestCase

from meresco.core import Observable

from seecr.test import CallTrace

from meresco.components.http import Deproxy, OnlyDeproxied

from weightless.core import compose, be, consume


class DeproxyTest(TestCase):
    def setUp(self):
        TestCase.setUp(self)

        self.createTree(deproxyForIps=["1.1.1.1"])

    def createTree(self, **kwargs):
        self.deproxy = Deproxy(**kwargs)
        self.observer = CallTrace("Observer", emptyGeneratorMethods=["handleRequest"])
        self.top = be(
            (
                Observable(),
                (
                    self.deproxy,
                    (self.observer,),
                ),
            )
        )

    def testShouldPassthroughHandleRequestIfUnconfigured(self):
        self.createTree()
        consume(
            self.top.all.handleRequest(
                Client=("9.1.8.2", 99), Headers={"H": "eaders"}, other="item"
            )
        )
        self.assertEqual(["handleRequest"], self.observer.calledMethodNames())
        (handleRequest,) = self.observer.calledMethods
        self.assertEqual(tuple(), handleRequest.args)
        self.assertEqual(
            dict(
                Client=("9.1.8.2", 99),
                Headers={"H": "eaders"},
                port=80,
                other="item",
                OriginalClient=None,
            ),
            handleRequest.kwargs,
        )

    def testClientInCaseNoXForwardedForHeader(self):
        list(compose(self.top.all.handleRequest(Client=("1.1.1.1", 11111), Headers={})))

        self.assertEqual(1, len(self.observer.calledMethods))
        handleRequestCallKwargs = self.observer.calledMethods[0].kwargs
        self.assertEqual("1.1.1.1", handleRequestCallKwargs["Client"][0])
        self.assertEqual({}, handleRequestCallKwargs["Headers"])

    def testDeproxy(self):
        list(
            compose(
                self.top.all.handleRequest(
                    Client=("1.1.1.1", 11111), Headers={"X-Forwarded-For": "2.2.2.2"}
                )
            )
        )

        self.assertEqual(1, len(self.observer.calledMethods))
        handleRequestCallKwargs = self.observer.calledMethods[0].kwargs
        self.assertEqual("2.2.2.2", handleRequestCallKwargs["Client"][0])
        self.assertEqual("1.1.1.1", handleRequestCallKwargs["OriginalClient"][0])
        self.assertEqual(
            {"X-Forwarded-For": "2.2.2.2"}, handleRequestCallKwargs["Headers"]
        )

    def testClientFromMulitpleXForwardedForEntries(self):
        list(
            compose(
                self.top.all.handleRequest(
                    Client=("1.1.1.1", 11111),
                    Headers={"X-Forwarded-For": "2.2.2.2,3.3.3.3,4.4.4.4"},
                )
            )
        )

        self.assertEqual(1, len(self.observer.calledMethods))
        handleRequestCallKwargs = self.observer.calledMethods[0].kwargs
        self.assertEqual("4.4.4.4", handleRequestCallKwargs["Client"][0])
        self.assertEqual(
            {"X-Forwarded-For": "2.2.2.2,3.3.3.3,4.4.4.4"},
            handleRequestCallKwargs["Headers"],
        )

        list(
            compose(
                self.top.all.handleRequest(
                    Client=("1.1.1.1", 11111),
                    Headers={"X-Forwarded-For": " 2.2.2.2 , 3.3.3.3, 4.4.4.4 ,"},
                )
            )
        )
        self.assertEqual("4.4.4.4", self.observer.calledMethods[1].kwargs["Client"][0])

    def testHostFromXForwardedHost(self):
        self.createTree(deproxyForIpRanges=[("9.9.9.0", "9.9.9.255")])
        Headers = {
            "Host": "1.1.1.1:11111",
            "X-Forwarded-Host": "2.2.2.2:22222,3.3.3.3:33333,4.4.4.4:44444",
        }
        consume(
            self.top.all.handleRequest(
                Client=("9.9.9.9", 9999), port=11111, Headers=Headers
            )
        )

        self.assertEqual(1, len(self.observer.calledMethods))
        handleRequestCallKwargs = self.observer.calledMethods[0].kwargs
        self.assertEqual("4.4.4.4:44444", handleRequestCallKwargs["Headers"]["Host"])
        self.assertEqual(44444, handleRequestCallKwargs["port"])

        Headers = {
            "Host": "1.1.1.1:11111",
            "X-Forwarded-Host": "2.2.2.2,3.3.3.3,4.4.4.4",
        }
        consume(
            self.top.all.handleRequest(
                Client=("9.9.9.9", 9999), port=11111, Headers=Headers
            )
        )

        self.assertEqual(2, len(self.observer.calledMethods))
        handleRequestCallKwargs = self.observer.calledMethods[1].kwargs
        self.assertEqual("4.4.4.4", handleRequestCallKwargs["Headers"]["Host"])
        self.assertEqual(80, handleRequestCallKwargs["port"])

    def testHostMultiple(self):
        self.createTree(deproxyForIpRanges=[("9.9.9.0", "9.9.9.255")])
        Headers = {
            "Host": ["1.1.1.1:11111", "4.4.4.4:44444"],
        }
        consume(
            self.top.all.handleRequest(
                Client=("9.9.9.9", 9999), port=11111, Headers=Headers
            )
        )

        self.assertEqual(1, len(self.observer.calledMethods))
        handleRequestCallKwargs = self.observer.calledMethods[0].kwargs
        self.assertEqual("4.4.4.4:44444", handleRequestCallKwargs["Headers"]["Host"])

    def testHostIPv6(self):
        self.createTree(deproxyForIpRanges=[("9.9.9.0", "9.9.9.255")])
        Headers = {
            "Host": ["[2001:88:99::11:22]:12345"],
        }
        consume(
            self.top.all.handleRequest(
                Client=("9.9.9.9", 9999), port=11111, Headers=Headers
            )
        )

        self.assertEqual(1, len(self.observer.calledMethods))
        handleRequestCallKwargs = self.observer.calledMethods[0].kwargs
        self.assertEqual(
            "[2001:88:99::11:22]:12345", handleRequestCallKwargs["Headers"]["Host"]
        )

    def testDeproxyForIps(self):
        self.createTree(deproxyForIps=["3.3.3.3"])
        consume(
            self.top.all.handleRequest(
                Client=("1.1.1.1", 11111), Headers={"X-Forwarded-For": "2.2.2.2"}
            )
        )

        self.assertEqual(1, len(self.observer.calledMethods))
        handleRequestCallKwargs = self.observer.calledMethods[0].kwargs
        self.assertEqual("1.1.1.1", handleRequestCallKwargs["Client"][0])
        self.assertEqual(
            {"X-Forwarded-For": "2.2.2.2"}, handleRequestCallKwargs["Headers"]
        )

    def testDeproxyUpdateIps(self):
        # Expose updateIps from IpFilter
        self.createTree(deproxyForIps=["127.7.7.7"])

        # White box
        allowDeproxying = lambda ip: self.deproxy._ipfilter.filterIpAddress(ip)
        self.assertEqual(True, allowDeproxying("127.7.7.7"))
        self.assertEqual(False, allowDeproxying("127.0.0.1"))
        self.assertEqual(False, allowDeproxying("10.0.0.1"))

        self.deproxy.updateIps(
            ipAddresses=["192.168.96.96"], ipRanges=[("10.0.0.0", "10.0.0.2")]
        )
        self.assertEqual(True, allowDeproxying("192.168.96.96"))
        self.assertEqual(True, allowDeproxying("10.0.0.1"))
        self.assertEqual(False, allowDeproxying("127.7.7.7"))
        self.assertEqual(False, allowDeproxying("127.0.0.1"))

        # Black box
        consume(
            self.top.all.handleRequest(
                Client=("192.168.96.96", 12345),
                Headers={
                    "X-Forwarded-For": "2.2.2.2",
                    "X-Forwarded-Host": "example.org",
                },
            )
        )

        self.assertEqual(1, len(self.observer.calledMethods))
        handleRequestCallKwargs = self.observer.calledMethods[0].kwargs
        self.assertEqual("2.2.2.2", handleRequestCallKwargs["Client"][0])
        self.assertEqual("192.168.96.96", handleRequestCallKwargs["OriginalClient"][0])
        self.assertEqual(
            {
                "X-Forwarded-For": "2.2.2.2",
                "X-Forwarded-Host": "example.org",
                "Host": "example.org",
            },
            handleRequestCallKwargs["Headers"],
        )

    def testOnlyDeproxied(self):
        odp = OnlyDeproxied()
        odp.addObserver(self.observer)
        consume(odp.handleRequest(path="/path"))
        self.assertEqual([], self.observer.calledMethodNames())

        consume(odp.handleRequest(path="/path", OriginalClient=("1.2.3.4", 1234)))
        self.assertEqual(["handleRequest"], self.observer.calledMethodNames())
        self.assertEqual(
            dict(path="/path", OriginalClient=("1.2.3.4", 1234)),
            self.observer.calledMethods[0].kwargs,
        )

    def testCurrentConfig(self):
        dep = Deproxy(
            deproxyForIps=["1.2.3.4", "2001:41c8:10:7c:aa:6:0:2"],
            deproxyForIpRanges=[
                "2001:41c8:10:7b::/64",
                "2001:41c8:10:7b::/128",
                "4.5.6.0/24",
                ("6.7.8.9", "6.7.8.90"),
            ],
        )
        self.assertEqual(
            [
                "IPAddress('1.2.3.4')",
                "IPAddress('2001:41c8:10:7c:aa:6:0:2')",
                "IPNetwork('2001:41c8:10:7b::/128')",
                "IPNetwork('2001:41c8:10:7b::/64')",
                "IPNetwork('4.5.6.0/24')",
                "IPRange('6.7.8.9', '6.7.8.90')",
            ],
            dep.current_config,
        )
        dep.updateIps(ipAddresses=["2.3.4.5"], ipRanges=["3.4.0.0/16"])
        self.assertEqual(
            [
                "IPAddress('2.3.4.5')",
                "IPNetwork('3.4.0.0/16')",
            ],
            dep.current_config,
        )
