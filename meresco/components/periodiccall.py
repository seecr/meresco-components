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

from traceback import print_exc

from weightless.core import compose, identify, Yield

from meresco.core import Observable


class PeriodicCall(Observable):
    def __init__(self, reactor, interval=3600, errorInterval=15, name=None):
        Observable.__init__(self, name=name)
        self._reactor = reactor
        self._interval = interval
        self._errorInterval = errorInterval

    def observer_init(self):
        self._reactor.addTimer(0, self._periodicCall)

    @identify
    def _periodicCall(self):
        this = yield  # this generator, from @identify
        self._reactor.addProcess(this.next)
        try:
            yield
            for _response in compose(self.all.handle()):
                if _response is not Yield and callable(_response):
                    _response(self._reactor, this.next)
                    yield
                    _response.resumeProcess()
                yield
        except (AssertionError, KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            print_exc()
            interval = self._errorInterval
        else:
            interval = self._interval
        finally:
            self._reactor.removeProcess()
            self._reactor.addTimer(interval, self._periodicCall)
            yield  # Done, wait for GC

