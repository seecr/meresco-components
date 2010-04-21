## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from time import strftime, gmtime
from sys import stdout, exc_info
from traceback import print_exc

class LogObserver(object):
    def __init__(self, stream = stdout, printtime = True):
        self.setStream(stream)
        self._printtime = printtime

    def setStream(self, stream):
        self._stream = stream
        self.write = self._stream.write
        self.flush = self._stream.flush


    def _write(self, aString):
        if self._printtime:
            self.write( '%s\t' % strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()))
        self.write('%s\n' % aString)
        self.flush()

    def unknown(self, method, *args, **kwargs):
        self._write("%s - %s" % (method, self.toString(*args)))

    def logException(self, exception='ignored'):
        print_exc(file=self._stream)

    def toString(self, *args):
        return '\t'.join(map(str, args))
