## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2011-2015, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

import sys
from functools import partial
from traceback import print_exc

from weightless.http import Acceptor as TcpAcceptor
from weightless.udp import Acceptor as UdpAcceptor
from meresco.core import Observable
from weightless.core import compose, Yield, identify


class _PacketListener(Observable):
    def __init__(self, reactor, port, acceptorClass):
        Observable.__init__(self)
        self._reactor = reactor
        self._port = port
        self._acceptorClass = acceptorClass
        self._acceptor = None

    def observer_init(self):
        def sinkFactory(sok):
            return lambda: self._handlePacket(sok)
        self._acceptor = self._acceptorClass(
            reactor=self._reactor,
            port=self._port,
            sinkFactory=sinkFactory)

    def close(self):
        if not self._acceptor is None:
            self._acceptor.close()

    def _handlePacket(self, sok):
        packet, remote = sok.recvfrom(2048)
        if type(self) is TcpPacketListener:
            while True:
                data = sok.recv(2048)
                if data == b'':
                    break
                packet += data
        if remote is None:
            remote = sok.getpeername()
        try:
            self._processPacket(packet.decode(), remote)
        finally:
            self.transmissionDone(sok)

    @identify
    def _processPacket(self, packet, remote):
        this = yield # this generator, from @identify
        self._reactor.addProcess(this.__next__)
        try:
            yield
            for _response in compose(self.all.handlePacket(data=packet, remote=remote)):
                if _response is not Yield and callable(_response):
                    _response(self._reactor, this.__next__)
                    yield
                    _response.resumeProcess()
                yield
        except (AssertionError, KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            print("Exception in _handlePacket for data=%s from %s" % (repr(packet), remote), file=sys.stderr)
            print_exc()
            sys.stderr.flush()
        finally:
            self._reactor.removeProcess()
        yield  # Done, wait for GC

    def transmissionDone(self, sok):
        pass


UdpPacketListener = partial(_PacketListener, acceptorClass=UdpAcceptor)


class TcpPacketListener(_PacketListener):
    def __init__(self, reactor, port):
        _PacketListener.__init__(self, reactor, port, acceptorClass=TcpAcceptor)

    def transmissionDone(self, sok):
        self._reactor.removeReader(sok)
        sok.close()
