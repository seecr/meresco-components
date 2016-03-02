## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 SURF http://www.surf.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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
from meresco.components import TimedDictionary
from weightless.core import compose
from utils import insertHeader
from hashlib import md5
from time import time
from random import randint, choice
from urllib import urlencode
from UserDict import UserDict
from string import ascii_letters
from seecr.zulutime import ZuluTime
from os.path import isfile
from .utils import findCookies

class Session(UserDict):
    def __init__(self, sessionId):
        d = {'id': sessionId}
        UserDict.__init__(self, d)

    def setLink(self, caption, key, value):
        return '<a href="?%s">%s</a>' % (urlencode({key: '+' + repr(value)}), caption)

    def unsetLink(self, caption, key, value):
        return '<a href="?%s">%s</a>' % (urlencode({key: '-' + repr(value)}), caption)

class SessionHandler(Observable):
    def __init__(self, secretSeed=None, nameSuffix='', timeout=3600*2):
        Observable.__init__(self)
        self._secretSeed = secretSeed or self.createSeed()
        self._cookieName = 'session' + nameSuffix
        self._timeout = timeout
        self._sessions = TimedDictionary(timeout)

    def handleRequest(self, RequestURI='', Client=None, Headers={}, arguments = {}, *args, **kwargs):
        sessionIds = findCookies(Headers=Headers, name=self._cookieName)
        session = None if len(sessionIds) <1 else self._sessions.get(sessionIds[0], None)

        if session is None:
            clientaddress, ignoredPort = Client
            sessionid = md5('%s%s%s%s' % (time(), randint(0, 9999999999), clientaddress, self._secretSeed)).hexdigest()
            session = Session(sessionid)
            self._sessions[session['id']] = session
        else:
            self._sessions.touch(session['id'])

        extraHeader = 'Set-Cookie: %s=%s; path=/; Expires=%s' % (self._cookieName, session['id'], self._zulutime().add(seconds=self._timeout).rfc1123())

        result = compose(self.all.handleRequest(session=session, arguments=arguments, RequestURI=RequestURI, Client=Client, Headers=Headers, *args, **kwargs))

        for response in insertHeader(result, extraHeader) :
            yield response

    def _zulutime(self):
        return ZuluTime()

    @staticmethod
    def createSeed():
        return ''.join(choice(ascii_letters) for i in xrange(20))

    @classmethod
    def seedFromFile(cls, filename):
        if isfile(filename):
            seed = open(filename).read().strip()
            if seed:
                return seed
        seed = cls.createSeed()
        with open(filename, 'w') as f:
            f.write(seed)
        return seed

#steps:
#Generate some kind of unique id. bijv. md5(time() + ip + secret_seed)
#set the cookie name,value pairs
    #some kind of escaping
#request cookie must be taken into consideration (if existing, don't generate a new session)
