## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012-2013, 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2016 SURFmarket https://surf.nl
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

from utils import notFoundHtml, redirectHttp, CRLF

from meresco.core import Transparent
from weightless.core import compose, Yield
from warnings import warn

class BasicHttpHandler(Transparent):
    def __init__(self, notFoundMethod=None, additionalHeaders=None):
        Transparent.__init__(self)
        self.notFound = self._notFound if notFoundMethod is None else notFoundMethod
        self._additionalHeaders = {} if additionalHeaders is None else additionalHeaders

    def handleRequest(self, **kwargs):
        yielded = False
        stuff = compose(self.all.handleRequest(**kwargs))
        for x in stuff:
            if x is Yield or callable(x):
                yield x
                continue

            if not yielded and CRLF in x:
                statusline, remainder = x.split(CRLF, 1)
                yield statusline + CRLF
                for key in self._additionalHeaders:
                    yield '{}: {}'.format(key, self._additionalHeaders[key]) + CRLF
                if remainder != '':
                    yield remainder
                yielded = True
            else:
                yield x



        if not yielded:
            try:
                result = self.notFound(**kwargs)
            except TypeError:
                warn("The 'notFoundMethod' should accept **kwargs", DeprecationWarning)
                result = self.notFound()
            yield result

    def _notFound(self, **kwargs):
        yield notFoundHtml
        yield "<html><body>404 Not Found</body></html>"

    @classmethod
    def createWithRedirect(cls, url):
        return cls(lambda **kwargs: redirectHttp % url)

