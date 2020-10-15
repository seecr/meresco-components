## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014 SURF http://www.surf.nl
# Copyright (C) 2014, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2014 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.core import Observable
from weightless.core import NoneOfTheObserversRespond, DeclineMessage, local
from traceback import print_exc


class LogCollector(Observable):
    """
    Collects logs from different 'loggers'.

    Typical Usage:
    ...
    (ObservableHttpServer(...),
        (LogCollector(),
            # Some logwriters, will listen to writeLog(**logItems)
            (ApachLogWriter(...),),
            (QueryLogWriter(...),),

            # Handling of http requests, with log appenders
            (...,
                (HandleRequestLog(),
                    ...,
                    (SruParser(...),
                        ...,
                        (SruHandler(enableLog=True, ...),
                            ...
                        )
                    )
                )
            )
        )
    )

    Writers, like ApacheLogWriter, work together with appenders,
    like HandleRequestLog. Make sure to align correctly.
    """

    def all_unknown(self, message, *args, **kwargs):
        try:
            __callstack_var_logCollector__ = self._logCollector()
            yield self.all.unknown(message, *args, **kwargs)
        finally:
            self._writeLog(__callstack_var_logCollector__)

    def any_unknown(self, message, *args, **kwargs):
        try:
            __callstack_var_logCollector__ = self._logCollector()
            try:
                response = yield self.any.unknown(message, *args, **kwargs)
            except NoneOfTheObserversRespond:
                raise DeclineMessage
            return response
        finally:
            self._writeLog(__callstack_var_logCollector__)

    def do_unknown(self, message, *args, **kwargs):
        try:
            __callstack_var_logCollector__ = self._logCollector()
            self.do.unknown(message, *args, **kwargs)
        finally:
            self._writeLog(__callstack_var_logCollector__)

    def call_unknown(self, message, *args, **kwargs):
        try:
            __callstack_var_logCollector__ = self._logCollector()
            try:
                return self.call.unknown(message, *args, **kwargs)
            except NoneOfTheObserversRespond:
                raise DeclineMessage
        finally:
            self._writeLog(__callstack_var_logCollector__)

    _logCollector = dict

    def _writeLog(self, collectedLog):
        if collectedLog:
            try:
                self.do.writeLog(collectedLog=collectedLog)
            except AssertionError:
                raise
            except Exception:
                print_exc()



class LogCollectorScope(Observable):
    def __init__(self, scopeName=None, name=None, **kwargs):
        if scopeName is None and name is None:
            raise TypeError("No name set for LogCollectorScope.")
        elif scopeName is None:
            scopeName = name
        if name is None:
            name = scopeName
        Observable.__init__(self, name=name, **kwargs)
        self._scopeName = scopeName

    def all_unknown(self, message, *args, **kwargs):
        myLogCollector = local('__callstack_var_logCollector__')
        try:
            __callstack_var_logCollector__ = LogCollector._logCollector()
            yield self.all.unknown(message, *args, **kwargs)
        finally:
            myLogCollector[self._scopeName] = __callstack_var_logCollector__

    def any_unknown(self, message, *args, **kwargs):
        myLogCollector = local('__callstack_var_logCollector__')
        try:
            __callstack_var_logCollector__ = LogCollector._logCollector()
            try:
                response = yield self.any.unknown(message, *args, **kwargs)
            except NoneOfTheObserversRespond:
                raise DeclineMessage
            return response
        finally:
            myLogCollector[self._scopeName] = __callstack_var_logCollector__

    def do_unknown(self, message, *args, **kwargs):
        myLogCollector = local('__callstack_var_logCollector__')
        try:
            __callstack_var_logCollector__ = LogCollector._logCollector()
            self.do.unknown(message, *args, **kwargs)
        finally:
            myLogCollector[self._scopeName] = __callstack_var_logCollector__

    def call_unknown(self, message, *args, **kwargs):
        myLogCollector = local('__callstack_var_logCollector__')
        try:
            __callstack_var_logCollector__ = LogCollector._logCollector()
            try:
                return self.call.unknown(message, *args, **kwargs)
            except NoneOfTheObserversRespond:
                raise DeclineMessage
        finally:
            myLogCollector[self._scopeName] = __callstack_var_logCollector__



def collectLog(*logDicts):
    collector=local('__callstack_var_logCollector__')
    for aLogDict in logDicts:
        for key, value in aLogDict.items():
            collector.setdefault(key, []).append(value)

def collectLogForScope(**scopes):
    for scope, aLogDict in scopes.items():
        collector=local('__callstack_var_logCollector__').setdefault(scope, dict())
        for key, value in aLogDict.items():
            collector.setdefault(key, []).append(value)
