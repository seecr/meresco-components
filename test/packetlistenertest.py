## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012-2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from unittest import TestCase
import sys
from socket import socket, AF_INET, SOCK_DGRAM
from StringIO import StringIO

from seecr.test import CallTrace
from weightless.core import compose, be
from meresco.core import Observable

from meresco.components.packetlistener import UdpPacketListener, TcpPacketListener


class PacketListenerTest(TestCase):
    def testUdpPacketListener(self):
        reactor = CallTrace('reactor')
        observer = CallTrace('observer', emptyGeneratorMethods=['handlePacket'])
        udpPacketListener = UdpPacketListener(reactor, port=1234)
        server = be((Observable(),
            (udpPacketListener,
                (observer,)
            )
        ))
        list(compose(server.once.observer_init()))

        self.assertEquals('addReader', reactor.calledMethods[0].name)
        handleCallback = reactor.calledMethods[0].args[1]
        sok = socket(AF_INET, SOCK_DGRAM)
        sok.sendto("TEST", ('localhost', 1234))
        sok.close()
        handleCallback()
        reactor.calledMethods[-1].args[0]()
        self.assertEquals(['observer_init', 'handlePacket'], observer.calledMethodNames())
        self.assertEquals("TEST", observer.calledMethods[1].kwargs['data'])

    def testTcpPacketListener(self):
        reactor = CallTrace('reactor')
        observer = CallTrace('observer', emptyGeneratorMethods=['handlePacket'])
        tcpPacketListener = TcpPacketListener(reactor, port=1234)
        server = be((Observable(),
            (tcpPacketListener,
                (observer,)
            )
        ))
        list(compose(server.once.observer_init()))

        self.assertEquals('addReader', reactor.calledMethods[0].name)
        acceptCallback = reactor.calledMethods[0].args[1]

        data = "TEST" * 1024
        sok = socket()
        sok.connect(('localhost', 1234))
        bytesSent = sok.send(data)
        self.assertEquals(len(data), bytesSent)
        sok.close()

        acceptCallback()
        self.assertEquals('addReader', reactor.calledMethods[1].name)
        handleCallback = reactor.calledMethods[1].args[1]
        handleCallback()
        self.assertEquals('addProcess', reactor.calledMethods[-2].name)
        reactor.calledMethods[-2].args[0]()

        self.assertEquals(['observer_init', 'handlePacket'], observer.calledMethodNames())
        self.assertEquals(data, observer.calledMethods[1].kwargs['data'])
        self.assertEquals('removeReader', reactor.calledMethods[-2].name)
        self.assertEquals('removeProcess', reactor.calledMethods[-1].name)

    def testExceptionInDownstreamHandlePacket(self):
        reactor = CallTrace()
        server = UdpPacketListener(reactor=reactor, port=1234)
        sok = CallTrace(returnValues={'recvfrom': ('data', ('127.0.0.1', 1234))})
        observer = CallTrace()
        observer.exceptions['handlePacket'] = Exception("This should be happening")
        server.addObserver(observer)

        mockStderr = StringIO()
        sys.stderr = mockStderr
        try:
            server._handlePacket(sok)
            reactor.calledMethods[-1].args[0]()
        finally:
            sys.stderr = sys.__stderr__
        lines = mockStderr.getvalue().split('\n')
        self.assertEquals("Exception in _handlePacket for data='data' from ('127.0.0.1', 1234)", lines[0])
        self.assertEquals('Traceback (most recent call last):', lines[1])
        self.assertEquals('Exception: This should be happening', lines[-2])
