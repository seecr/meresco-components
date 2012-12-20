## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2012 Stichting Kennisnet http://www.kennisnet.nl
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

from seecr.test import SeecrTestCase, CallTrace

from os.path import join, dirname

from meresco.components.http import ObservableHttpsServer

testDataDir = join(dirname(dirname(__file__)), 'data', 'ssl')

class ObservableHttpsServerTest(SeecrTestCase):

    def testCompressResponseFlag(self):
        reactor = CallTrace('Reactor')

        keyfile = join(testDataDir, 'server.pkey')
        certfile = join(testDataDir, 'server.cert')
        mockSok = object()

        s = ObservableHttpsServer(reactor, 0, keyfile=keyfile, certfile=certfile, compressResponse=True)
        s.startServer()
        httpsserver_acceptor = s._httpsserver._acceptor
        httpHandler = httpsserver_acceptor._sinkFactory(mockSok)
        self.assertEquals(True, httpHandler._compressResponse)

        s = ObservableHttpsServer(reactor, 0, keyfile=keyfile, certfile=certfile, bindAddress='127.0.0.1')
        s.startServer()
        httpsserver_acceptor = s._httpsserver._acceptor
        httpHandler = httpsserver_acceptor._sinkFactory(mockSok)
        self.assertEquals(False, httpHandler._compressResponse)
        self.assertEquals('127.0.0.1', httpsserver_acceptor._sok.getsockname()[0])

