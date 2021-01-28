# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from weightless.core import NoneOfTheObserversRespond, DeclineMessage
from meresco.core import Observable


class Converter(Observable):
    def __init__(self, fromKwarg, toKwarg=None, name=None):
        if not fromKwarg:
            raise ValueError("'fromKwarg' should contain a keyword argument name.")
        Observable.__init__(self, name=name)
        self._fromKwarg = fromKwarg
        self._toKwarg = toKwarg if toKwarg else self._fromKwarg

    def all_unknown(self, msg, *args, **kwargs):
        newArgs, newKwargs = self._convertArgs(*args, **kwargs)
        yield self.all.unknown(msg, *newArgs, **newKwargs)

    def any_unknown(self, msg, *args, **kwargs):
        newArgs, newKwargs = self._convertArgs(*args, **kwargs)
        try:
            response = yield self.any.unknown(msg, *newArgs, **newKwargs)
            return response
        except NoneOfTheObserversRespond:
            raise DeclineMessage

    def do_unknown(self, msg, *args, **kwargs):
        newArgs, newKwargs = self._convertArgs(*args, **kwargs)
        self.do.unknown(msg, *newArgs, **newKwargs)

    def call_unknown(self, msg, *args, **kwargs):
        newArgs, newKwargs = self._convertArgs(*args, **kwargs)
        try:
            return self.call.unknown(msg, *newArgs, **newKwargs)
        except NoneOfTheObserversRespond:
            raise DeclineMessage

    def _convertArgs(self, *args, **kwargs):
        try:
            oldvalue = kwargs[self._fromKwarg]
        except KeyError:
            pass
        else:
            del kwargs[self._fromKwarg]
            kwargs[self._toKwarg] = self._convert(oldvalue)
        return args, kwargs

    def _convert(self, anObject):
        raise NotImplementedError()

