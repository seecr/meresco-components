## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2012 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.components import Converter, IteratorAsStream
from zlib import compress as _compress, decompress, decompressobj as DeflateDecompressObj, compressobj as DeflateCompressObj
from base64 import encodebytes, decodebytes
from weightless.core import compose
from meresco.core import Transparent
from io import BytesIO

from weightless.core import compose, Yield
import collections

compress = lambda data: _compress(data)

class _OutboundConverter(Transparent):
    def yieldRecord(self, *args, **kwargs):
        for stuff in self.getStream(*args, **kwargs):
            yield stuff

    def getStream(self, *args, **kwargs):
        return BytesIO(self._convert(self.call.getStream(*args, **kwargs).read()))


class ZipInbound(Converter):
    def _convert(self, data):
        return compress(data)

class _DeflateIterator(object):
    def __init__(self, aStream, deflateClass, deflateMethodName):
        self.__aStream = aStream
        self._deflateObject = deflateClass()
        self._deflateMethod = getattr(self._deflateObject, deflateMethodName)

    def __iter__(self):
        for data in self.__aStream:
            yield self._deflateMethod(data if type(data) == bytes else data.encode())
        f = self._deflateObject.flush()
        if f:
            yield f

class _DeflateOutbound(Transparent):
    def yieldRecord(self, *args, **kwargs):
        allCall = compose(self.all.yieldRecord(*args, **kwargs))
        deflateObject = self.deflateClass()
        deflate = getattr(deflateObject, self.deflateMethodName)
        for data in allCall:
            if data is Yield or isinstance(data, collections.Callable):
                yield data
                continue
            yield deflate(data if type(data) == bytes else data.encode())
        f = deflateObject.flush()
        if f:
            yield f

    def getStream(self, *args, **kwargs):
        return IteratorAsStream(
                _DeflateIterator(
                    self.call.getStream(*args, **kwargs),
                    deflateClass=self.deflateClass,
                    deflateMethodName=self.deflateMethodName
                )
            )

class ZipOutbound(_DeflateOutbound):
    deflateClass = DeflateCompressObj
    deflateMethodName = "compress"

class UnzipOutbound(_DeflateOutbound):
    deflateClass = DeflateDecompressObj
    deflateMethodName = "decompress"

class UnzipInbound(Converter):
    def _convert(self, data):
        return decompress(data)

class Base64DecodeInbound(Converter):
    def _convert(self, data):
        return decodebytes(data)

class Base64DecodeOutbound(_OutboundConverter):
    def _convert(self, data):
        return decodebytes(data)

class Base64EncodeInbound(Converter):
    def _convert(self, data):
        return encodebytes(data)

class Base64EncodeOutbound(_OutboundConverter):
    def _convert(self, data):
        return encodebytes(data)

