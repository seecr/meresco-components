## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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
from base64 import b64decode

class BasicAuthentication(Observable):

    def __init__(self, realm):
        Observable.__init__(self)
        self._realm = realm

    def handleRequest(self, Headers={}, *args, **kwargs):
        relevantHeader = Headers.get('Authorization', None)
        if relevantHeader == None:
            yield REQUEST_AUTHENTICATION_RESPONSE % (self._realm, 'Please give username and password.')
            return
        username, password = self._parseHeader(relevantHeader)
        if not self.call.isValidLogin(username, password):
            yield REQUEST_AUTHENTICATION_RESPONSE % (self._realm, 'Username or password are not valid.')
            return
        user = self.call.getUser(username)
        yield self.all.handleRequest(Headers=Headers, user=user, *args, **kwargs)

    def _parseHeader(self, header):
        if type(header) is str:
            header = bytes(header, encoding="utf-8")

        parts = header.split()
        if len(parts) != 2:
            return None

        part0, b64encoded = parts
        if part0 != b"Basic":
            return None

        parts = b64decode(b64encoded).split(b":", 1)
        if len(parts) != 2:
            return None
        username, password = parts

        return username.decode(), password.decode()

REQUEST_AUTHENTICATION_RESPONSE = '\r\n'.join(
    [
        'HTTP/1.0 401 UNAUTHORIZED',
        'Content-Type: text/plain; charset=utf-8',
        'WWW-Authenticate: Basic realm="%s"',
        '',
        '%s'
    ])
