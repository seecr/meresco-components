## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
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

from socket import socket, error as SocketError, SHUT_WR, SHUT_RD, SOL_SOCKET, SO_ERROR
from errno import EINPROGRESS, ECONNREFUSED
from traceback import format_exc
from os import makedirs, close, remove
from os.path import join, isfile, isdir
from urllib import urlencode

from meresco.core import Observable
from meresco.components.http.utils import CRLF
from weightless.core import compose, Yield

from sys import stderr, stdout
from time import time
from tempfile import TemporaryFile

class PeriodicDownload(Observable):
    def __init__(self, reactor, host, port, period=1, verbose=False, prio=None, err=None):
        super(PeriodicDownload, self).__init__()
        self._reactor = reactor
        self._host = host
        self._port = port 
        self._period = period
        self._prio = prio
        self._err = err or stderr
        if not verbose:
            self._log = lambda x: None

    def observer_init(self):
        self.startTimer()

    def startTimer(self, additionalTime=0):
        self._reactor.addTimer(self._period + additionalTime, self.startProcess)

    def startProcess(self):
        self._processOne = compose(self.processOne())
        self._processOne.next()

    def processOne(self):
        sok = yield self._tryConnect()
        requestString = self.call.buildRequest()
        sok.send(requestString)
        sok.shutdown(SHUT_WR)
        self._reactor.addReader(sok, self._processOne.next, prio=self._prio)
        responses = []
        try:
            try:
                while True:
                    yield
                    response = sok.recv(4096)
                    if response == '':
                         break
                    responses.append(response)
            finally:
                self._reactor.removeReader(sok)
                sok.close()
        except SocketError, (errno, msg):
            yield self._retryAfterError("Receive error: %s: %s" % (errno, msg), request=requestString)
            return

        try:
            response = ''.join(responses)
            headers, body = response.split(2 * CRLF, 1)
            statusLine = headers.split(CRLF)[0]
            if not statusLine.strip().lower().endswith('200 ok'):
                yield self._retryAfterError('Unexpected response: ' + statusLine, request=requestString)
                return

            self._reactor.addProcess(self._processOne.next)
            yield
            try:
                gen = self.all.handle(data=body)
                g = compose(gen)
                for response  in g:
                    if callable(response) and not response is Yield:
                        response(self._reactor, self._processOne.next)
                        yield
                        response.resumeProcess()
                    yield
            finally:
                self._reactor.removeProcess()
        except (AssertionError, KeyboardInterrupt, SystemExit), e:
            raise
        except Exception:
            self._logError(format_exc())
        self.startTimer()
        yield

    def _tryConnect(self):
        sok = socket()
        sok.setblocking(0)
        while True:
            try:
                try:
                    sok.connect((self._host, self._port))
                except SocketError, (errno, msg):
                    if errno != EINPROGRESS:
                        yield self._retryAfterError("%s: %s" % (errno, msg))
                        continue
                self._reactor.addWriter(sok, self._processOne.next)
                yield
                self._reactor.removeWriter(sok)

                err = sok.getsockopt(SOL_SOCKET, SO_ERROR)
                if err == ECONNREFUSED:
                    yield self._retryAfterError("Connection refused.")
                    continue
                if err != 0:   # any other error
                    raise IOError(err)
                break
            except (AssertionError, KeyboardInterrupt, SystemExit), e:
                raise
            except Exception, e:
                yield self._retryAfterError(str(e), additionalTime=5*60)
                continue
        raise StopIteration(sok)

    def _retryAfterError(self, message, request=None, additionalTime=0):
        self._logError(message, request)
        self.startTimer(additionalTime=additionalTime)
        yield
        
    def _logError(self, message, request=None):
        self._err.write("%s:%s: " % (self._host, self._port))
        self._err.write(message)
        if not message.endswith('\n'):
            self._err.write('\n')
        if request:
            self._err.write('For request: ')
            self._err.write(request)
            if not request.endswith('\n'):
                self._err.write('\n')
        self._err.flush()

    def _log(self, message):
        stdout.write(message)
        if not message.endswith('\n'):
            stdout.write('\n')
        stdout.flush()

