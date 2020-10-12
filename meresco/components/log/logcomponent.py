## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2011 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
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
from lxml.etree import _ElementTree as ElementTreeType

from weightless.core import NoneOfTheObserversRespond, DeclineMessage
from meresco.core import Observable
from meresco.components import lxmltostring


class LogComponent(Observable):
    def _log(self, message, *args, **kwargs):
        printKwargs = dict(kwargs)
        for key, value in kwargs.items():
            if type(value) == ElementTreeType:
                printKwargs[key] = "%s(%s)" % (value.__class__.__name__, lxmltostring(value))
        sys.stdout.write("[%s] %s(*%s, **%s)\n" % (self.observable_name(), message, args, printKwargs))
        sys.stdout.flush()

    def all_unknown(self, message, *args, **kwargs):
        self._log(message, *args, **kwargs)
        yield self.all.unknown(message, *args, **kwargs)

    def any_unknown(self, message, *args, **kwargs):
        self._log(message, *args, **kwargs)
        try:
            response = yield self.any.unknown(message, *args, **kwargs)
        except NoneOfTheObserversRespond:
            raise DeclineMessage
        raise StopIteration(response)

    def do_unknown(self, message, *args, **kwargs):
        self._log(message, *args, **kwargs)
        self.do.unknown(message, *args, **kwargs)

    def call_unknown(self, message, *args, **kwargs):
        self._log(message, *args, **kwargs)
        try:
            return self.call.unknown(message, *args, **kwargs)
        except NoneOfTheObserversRespond:
            raise DeclineMessage
