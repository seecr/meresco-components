## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011, 2013-2014 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012, 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from socket import socket, error as SocketError, SHUT_WR, SOL_SOCKET, SO_ERROR, SOL_TCP, TCP_KEEPINTVL, TCP_KEEPIDLE, TCP_KEEPCNT, SO_KEEPALIVE
from errno import EINPROGRESS, ECONNREFUSED
from traceback import format_exc

from meresco.core import Observable
from meresco.components.http.utils import CRLF
from schedule import Schedule
from weightless.core import compose, Yield

from sys import stderr
from warnings import warn


class PeriodicDownload(Observable):
    def __init__(self, reactor, host=None, port=None, period=None, verbose=None, prio=None, name=None, err=None, autoStart=True, schedule=None):
        super(PeriodicDownload, self).__init__(name=name)
        self._reactor = reactor
        self._host = host
        self._port = port
        self._schedule = schedule
        if schedule is None:
            if period is None:
                period = 1
            else:
                warn("Please use schedule instead of period.", DeprecationWarning) # since 2013-02-20
            self._schedule = Schedule(period=period)
        elif not period is None:
            raise ValueError("Using both schedule and period is invalid")
        self._prio = prio
        self._err = err or stderr
        self._paused = not autoStart
        self._currentTimer = None
        self._currentProcess = None
        self._sok = None
        self._errorState = None
        if autoStart and (not self._host or not self._port):
            raise ValueError("Unless autoStart is set to False host and port need to be specified.")
        if verbose in [True, False]:
            warn('Verbose flag is deprecated', DeprecationWarning)

    def getState(self):
        return PeriodicDownloadStateView(self)

    def setDownloadAddress(self, host, port):
        self._host = host
        self._port = port

    def setSchedule(self, schedule):
        if self._schedule != schedule:
            self._schedule = schedule
            self._stopTimer()
            if not self._currentProcess:
                self._startTimer()

    def setPeriod(self, period):
        warn("Please use setSchedule(...)", DeprecationWarning)
        self.setSchedule(Schedule(period=period))

    def pause(self):
        if self._paused:
            return
        self._stopTimer()
        if self._sok:
            self._reactor.removeReader(self._sok)
            self._currentProcess = None
            # Note: generator will receive GeneratorExit from garbage collector, triggering
            # 'finally' block after self._sok.recv(...) where sok will be closed.
        self._paused = True
        self._logInfo("paused")

    def resume(self):
        if not self._paused:
            return
        self._paused = False
        if not self._currentProcess:
            self._startTimer()
        self._logInfo("resumed")

    def observer_init(self):
        self._startTimer()


    def _startTimer(self, retryAfter=None):
        self._currentProcess = None
        if not self._paused:
            t = self._schedule.secondsFromNow() if retryAfter is None else retryAfter
            self._currentTimer = self._reactor.addTimer(t, self._startProcess)

    def _stopTimer(self):
        if not self._currentTimer:
            return
        try:
            self._reactor.removeTimer(self._currentTimer)
        except KeyError:
            pass
        self._currentTimer = None

    def _startProcess(self):
        self._currentTimer = None
        self._currentProcess = compose(self._processOne())
        self._currentProcess.next()

    def _processOne(self):
        additionalHeaders = {'Host': self._host} if self._host else {}
        request = self.call.buildRequest(additionalHeaders=additionalHeaders)
        if type(request) is tuple:
            host, port, requestString = request
        else:
            host = self._host
            port = self._port
            requestString = request
        if requestString is None:
            self._startTimer(retryAfter=1)
            yield
            return
        self._sok = yield self._tryConnect(host, port)
        try:
            self._sok.send(requestString)
            self._sok.shutdown(SHUT_WR)
            self._reactor.addReader(self._sok, self._currentProcess.next, prio=self._prio)
            responses = []
            try:
                while True:
                    yield
                    response = self._sok.recv(4096)
                    if response == '':
                         break
                    responses.append(response)
            finally:
                try:
                    self._reactor.removeReader(self._sok)
                except KeyError:
                    pass
        except SocketError, (errno, msg):
            yield self._retryAfterError("Receive error: %s: %s" % (errno, msg), request=requestString, retryAfter=30)
            return
        finally:
            self._sok.close()
            self._sok = None

        try:
            response = ''.join(responses)
            headers, body = response.split(2 * CRLF, 1)
            statusLine = headers.split(CRLF)[0]
            if not statusLine.strip().lower().endswith('200 ok'):
                yield self._retryAfterError('Unexpected response: ' + response, request=requestString, retryAfter=30)
                return

            self._reactor.addProcess(self._currentProcess.next)
            yield
            try:
                gen = self.all.handle(data=body)
                g = compose(gen)
                for _response  in g:
                    if callable(_response) and not _response is Yield:
                        _response(self._reactor, self._currentProcess.next)
                        yield
                        _response.resumeProcess()
                    yield
            finally:
                self._reactor.removeProcess()
        except (AssertionError, KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            message = format_exc()
            message += 'Error while processing response: ' + _shorten(response)
            self._logError(message, request=requestString)
        self._errorState = None
        self._startTimer()
        yield

    def _tryConnect(self, host, port):
        sok = socket()
        sok.setblocking(0)
        sok.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
        sok.setsockopt(SOL_TCP, TCP_KEEPIDLE, 60*10)
        sok.setsockopt(SOL_TCP, TCP_KEEPINTVL, 75)
        sok.setsockopt(SOL_TCP, TCP_KEEPCNT, 9)
        while True:
            try:
                try:
                    sok.connect((host, port))
                except SocketError, (errno, msg):
                    if errno != EINPROGRESS:
                        yield self._retryAfterError("%s: %s" % (errno, msg))
                        return
                self._reactor.addWriter(sok, self._currentProcess.next)
                yield
                self._reactor.removeWriter(sok)

                err = sok.getsockopt(SOL_SOCKET, SO_ERROR)
                if err == ECONNREFUSED:
                    yield self._retryAfterError("Connection refused.", retryAfter=1)
                    return
                if err != 0:   # any other error
                    raise IOError(err)
                break
            except (AssertionError, KeyboardInterrupt, SystemExit), e:
                raise
            except Exception, e:
                yield self._retryAfterError(str(e), retryAfter=5*60)
                return
        raise StopIteration(sok)

    def _retryAfterError(self, message, request=None, retryAfter=0.1):
        self._errorState = message
        self._logError(message, request)
        self._startTimer(retryAfter=retryAfter)
        yield

    def _logError(self, message, request=None):
        self._log(self._err, message, request)

    def _logInfo(self, message):
        self._log(self._err, message)

    def _log(self, out, message, request=None):
        out.write("%s: " % repr(self))
        out.write(message)
        if not message.endswith('\n'):
            out.write('\n')
        if request:
            out.write('For request: ')
            out.write(request)
            if not request.endswith('\n'):
                out.write('\n')
        out.flush()

    def __repr__(self):
        kwargsList = [
            '%s=%s' % (name, repr(getattr(self, '_%s' % name)))
            for name in ['host', 'port', 'prio', 'name', 'schedule']
            if getattr(self, '_%s' % name, None)
        ]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(kwargsList))


class PeriodicDownloadStateView(object):
    def __init__(self, periodicDownload):
        self._periodicDownload = periodicDownload
        self._name = self._periodicDownload.observable_name()

    @property
    def name(self):
        return self._name

    @property
    def host(self):
        return self._periodicDownload._host

    @property
    def port(self):
        return self._periodicDownload._port

    @property
    def paused(self):
        return self._periodicDownload._paused

    @property
    def period(self):
        warn("Please use schedule.", DeprecationWarning)
        return self.schedule.secondsFromNow()

    @property
    def schedule(self):
        return self._periodicDownload._schedule

    @property
    def errorState(self):
        return self._periodicDownload._errorState

MAX_LENGTH=1500
def _shorten(response):
    if len(response) < MAX_LENGTH:
        return response
    headLength = 2*MAX_LENGTH/3
    tailLength = MAX_LENGTH - headLength
    return "%s ... %s" % (response[:headLength], response[-tailLength:])
