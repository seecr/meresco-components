## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from meresco.core import Observable
from meresco.components import TimedDictionary
from utils import insertHeader
from md5 import md5
from time import time
from random import randint
from urllib import urlencode
from urlparse import urlsplit
from cgi import parse_qs
from UserDict import UserDict

class Session(UserDict):
    def __init__(self, sessionId):
        d = {'id': sessionId}
        UserDict.__init__(self, d)

    def setLink(self, caption, key, value):
        return '<a href="?%s">%s</a>' % (urlencode({key: '+' + repr(value)}), caption)

    def unsetLink(self, caption, key, value):
        return '<a href="?%s">%s</a>' % (urlencode({key: '-' + repr(value)}), caption)

class SessionHandler(Observable):
    def __init__(self, secretSeed, nameSuffix='', timeout=3600*2):
        Observable.__init__(self)
        self._secretSeed = secretSeed
        self._nameSuffix = nameSuffix
        self._sessions = TimedDictionary(timeout)

    def handleRequest(self, RequestURI='', Client=None, Headers={}, arguments = {}, *args, **kwargs):
        sessioncookies = [cookie.strip() for cookie in Headers.get('Cookie','').split(';') if cookie.strip().startswith('session%s=' % self._nameSuffix)]
        sessionid, session = None, None
        if len(sessioncookies) >=1:
            sessionid = sessioncookies[0].split('=')[1]
            session = self._sessions.get(sessionid, None)

        if session == None:
            clientaddress, ignoredPort = Client
            sessionid = md5('%s%s%s%s' % (time(), randint(0, 9999999999), clientaddress, self._secretSeed)).hexdigest()
            session = Session(sessionid)
            self._sessions[sessionid] = session

        extraHeader = 'Set-Cookie: session%s=%s; path=/' % (self._nameSuffix, sessionid)

        result = self.all.handleRequest(session=session, arguments=arguments, RequestURI=RequestURI, Client=Client, Headers=Headers, *args, **kwargs)

        for response in insertHeader(result, extraHeader) :
            yield response

#steps:
#Generate some kind of unique id. bijv. md5(time() + ip + secret_seed)
#set the cookie name,value pairs
    #some kind of escaping
#request cookie must be taken into consideration (if existing, don't generate a new session)
