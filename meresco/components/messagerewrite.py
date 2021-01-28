## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from weightless.core import DeclineMessage, NoneOfTheObserversRespond
from meresco.core import Observable


class MessageRewrite(Observable):
    def __init__(self, fromMessage, toMessage, **kwargs):
        Observable.__init__(self, **kwargs)
        self._fromMessage = fromMessage
        self._toMessage = toMessage

    def all_unknown(self, message, *args, **kwargs):
        message = self._rewrite(message)
        yield self.all.unknown(message, *args, **kwargs)

    def any_unknown(self, message, *args, **kwargs):
        message = self._rewrite(message)
        try:
            response = yield self.any.unknown(message, *args, **kwargs)
        except NoneOfTheObserversRespond:
            raise DeclineMessage
        return response

    def do_unknown(self, message, *args, **kwargs):
        message = self._rewrite(message)
        self.do.unknown(message, *args, **kwargs)

    def call_unknown(self, message, *args, **kwargs):
        message = self._rewrite(message)
        try:
            return self.call.unknown(message, *args, **kwargs)
        except NoneOfTheObserversRespond:
            raise DeclineMessage

    def _rewrite(self, message):
        if message == self._fromMessage:
            message = self._toMessage
        return message
