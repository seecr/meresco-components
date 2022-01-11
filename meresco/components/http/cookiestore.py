## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2016, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from uuid import uuid4
from meresco.components import TimedDictionary, TimedPersistentDictionary
from time import time
from email.utils import formatdate

TWO_WEEKS = 2*7*24*60*60

SECURE = "Secure"
HTTPONLY = "HttpOnly"

def CookieMemoryStore(timeout, *args, **kwargs):
    return CookieStore(TimedDictionary(timeout), timeout, *args, **kwargs)

def CookiePersistentStore(timeout, filename, *args, **kwargs):
    return CookieStore(TimedPersistentDictionary(timeout, filename=filename), timeout, *args, **kwargs)

class CookieStore(object):
    def __init__(self, store, timeout, name=None, secure=False, httpOnly=True,):
        self._timeout = timeout
        self._store = store
        self._name = '{0}{1}'.format('' if name is None else '%s-' % name, store.id())
        self._secure = secure
        self._httpOnly = httpOnly

    def createCookie(self, anObject):
        cookie = str(uuid4())
        cookieValues = dict(value=anObject)
        cookieValues[SECURE] = self._secure
        cookieValues[HTTPONLY] = self._httpOnly
        self._store[cookie] = cookieValues
        return self._result(cookie)

    def removeCookie(self, cookie):
        try:
            del self._store[cookie]
        except KeyError:
            pass

    def removeCookies(self, filter):
        for k in list(self._store.keys()):
            try:
                if filter(self._store.peek(k)['value']):
                    del self._store[k]
            except (AttributeError, KeyError):
                pass

    def validateCookie(self, cookie):
        cookieInfo = self._store.get(cookie)
        if cookieInfo is not None and cookieInfo['value'] is not None:
            self._store.touch(cookie)
            return self._result(cookie)
        return None

    def cookieName(self):
        return self._name

    def _result(self, cookie):
        cookieInfo = self._store.get(cookie)
        values = ["{0}={1}".format(*i) for i in [
            (self._name, cookie),
            ('path', '/'),
            ('expires', formatdate(self._now() + self._timeout, usegmt=True))]]
        values.extend(k for k in [SECURE, HTTPONLY] if cookieInfo.get(k) == True)

        return dict(
            cookie=cookie,
            value=cookieInfo['value'],
            header='Set-Cookie: {0}'.format('; '.join(values)))


    def _now(self):
        return time()
