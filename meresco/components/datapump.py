## begin license ##
# 
# "Edurep" is a service for searching in educational repositories.
# "Edurep" is developed for Stichting Kennisnet (http://www.kennisnet.nl) by
# Seek You Too (http://www.cq2.nl). The project is based on the opensource
# project Meresco (http://www.meresco.com). 
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Kennisnet http://www.kennisnet.nl
# 
# This file is part of "Edurep"
# 
# "Edurep" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Edurep" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Edurep"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from meresco.components import Converter
from zlib import compress as _compress, decompress
from base64 import encodestring, decodestring
from weightless.core import compose
from meresco.core import Observable
from StringIO import StringIO

compress = lambda data: _compress(data)

class _OutboundConverter(Observable):
    def yieldRecord(self, *args, **kwargs):
        for stuff in self.getStream(*args, **kwargs):
            yield stuff

    def isAvailable(self, *args, **kwargs):
        return self.call.isAvailable(*args, **kwargs)

    def getStream(self, *args, **kwargs):
        return StringIO(self._convert(self.call.getStream(*args, **kwargs).read()))


class ZipInbound(Converter):
    def _convert(self, data):
        return compress(data)

class ZipOutbound(_OutboundConverter):
    def _convert(self, data):
        return compress(data)

class UnzipInbound(Converter):
    def _convert(self, data):
        return decompress(data)

class UnzipOutbound(_OutboundConverter):
    def _convert(self, data):
        return decompress(data)

class Base64DecodeInbound(Converter):
    def _convert(self, data):
        return decodestring(data)

class Base64DecodeOutbound(_OutboundConverter):
    def _convert(self, data):
        return decodestring(data)

class Base64EncodeInbound(Converter):
    def _convert(self, data):
        return encodestring(data)

class Base64EncodeOutbound(_OutboundConverter):
    def _convert(self, data):
        return encodestring(data)

