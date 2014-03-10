## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from traceback import format_exc

from weightless.core import compose, identify, Yield

from meresco.core import Observable

from schedule import Schedule


class PeriodicCall(Observable):
    def __init__(self, reactor, message=None, initialSchedule=None, schedule=None, errorSchedule=Schedule(period=15), autoStart=True, prio=None, name=None):
        Observable.__init__(self, name=name)
        self._reactor = reactor
        self._message = message or 'handle'
        self._initialSchedule = initialSchedule
        self._schedule = schedule
        self._errorSchedule = errorSchedule
        # Pause as soon as possible, please.
        self._pause = not autoStart
        self._prio = prio

        self._busy = False
        self._currentTimer = None

        if not (self._pause or self._schedule):
            raise ValueError('When autoStart is enabled, a schedule is required.')

    def observer_init(self):
        if self._pause:
            return
        interval = None
        if self._initialSchedule:
            interval = self._initialSchedule.secondsFromNow()
        self._addTimer(interval)

    def pause(self):
        self._pause = True
        if self._currentTimer:
            self._removeTimer()
            self._log('paused')

    def resume(self):
        if not self._pause:
            return

        self._pause = False
        if not self._busy:
            self._addTimer()

        self._log('resumed')

    def setSchedule(self, schedule):
        if self._schedule == schedule:
            return

        self._schedule = schedule
        if self._currentTimer:
            self._removeTimer()
            self._addTimer()

    def getState(self):
        return PeriodicCallStateView(self)

    @identify
    def _periodicCall(self):
        this = yield  # this generator, from @identify
        self._busy = True
        self._currentTimer = None
        interval = None  # default
        self._reactor.addProcess(this.next, prio=self._prio)
        try:
            yield
            for _response in compose(self.all.unknown(message=self._message)):
                if _response is not Yield and callable(_response):
                    _response(self._reactor, this.next)
                    yield
                    _response.resumeProcess()
                yield
        except (AssertionError, KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self._log(format_exc())
            interval = self._errorSchedule.secondsFromNow()
        finally:
            self._reactor.removeProcess()
            if not self._pause:
                self._addTimer(interval)
            else:
                self._log('paused')
            self._busy = False

        yield  # Done, wait for GC

    def _addTimer(self, interval=None):
        interval = interval if interval is not None else self._schedule.secondsFromNow()
        self._currentTimer = self._reactor.addTimer(interval, self._periodicCall)

    def _removeTimer(self):
        self._reactor.removeTimer(self._currentTimer)

    def _log(self, message):
        sys.stderr.write("%s: " % repr(self))
        sys.stderr.write(message)
        if not message.endswith('\n'):
            sys.stderr.write('\n')
        sys.stderr.flush()

    def __repr__(self):
        stateDict = PeriodicCallStateView(self).asDict()
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join(
                '%s=%s' % (k, repr(v))
                for (k, v) in sorted(stateDict.items())
                if v is not None
            )
        )


class PeriodicCallStateView(object):
    def __init__(self, periodicCall):
        self._periodicCall = periodicCall

    @property
    def name(self):
        return self._periodicCall.observable_name()

    @property
    def paused(self):
        return self._periodicCall._pause and not self._periodicCall._busy

    @property
    def schedule(self):
        return self._periodicCall._schedule

    def asDict(self):
        return {
            'name': self.name,
            'paused': self.paused,
            'schedule': self.schedule,
        }


MAX_LENGTH=1500
def shorten(response):
    if len(response) < MAX_LENGTH:
        return response
    headLength = 2*MAX_LENGTH/3
    tailLength = MAX_LENGTH - headLength
    return "%s ... %s" % (response[:headLength], response[-tailLength:])

