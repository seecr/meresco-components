## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014, 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2014 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.core import Transparent
from meresco.components.log import collectLogForScope
from weightless.core import compose, Yield
from time import time
from sys import exc_info

class HandleRequestLog(Transparent):
    def handleRequest(self, **kwargs):
        requestLogDict = dict()
        responseLogDict = dict()
        timestamp = self._time()
        requestLogDict['timestamp'] = timestamp
        for key in ['Client', 'Headers', 'RequestURI', 'Method', 'HTTPVersion', 'path', 'query', 'arguments']:
            if key in kwargs:
                requestLogDict[key] = kwargs[key]
        body = kwargs.get('Body')
        if body:
            requestLogDict['bodySize'] = len(body)
        sizeInBytes = 0
        httpStatus = ""

        try:
            for response in compose(self.all.handleRequest(**kwargs)):
                if response is Yield or callable(response):
                    yield response
                    continue
                if hasattr(response, '__len__'):
                    sizeInBytes += len(response)
                    if not httpStatus and response.startswith('HTTP/1'):
                        httpStatus = response[len('HTTP/1.0 '):][:3]
                yield response
        except (SystemExit, KeyboardInterrupt, AssertionError):
            raise
        except:
            _, errorValue, _  = exc_info()
            responseLogDict['size'] = sizeInBytes or '-'
            responseLogDict['httpStatus'] = httpStatus or '500'  # assuming this is what HttpServer will make of it
            responseLogDict['duration'] = self._time() - timestamp
            responseLogDict['exception'] = errorValue
            collectLogForScope(httpRequest=requestLogDict, httpResponse=responseLogDict)
            raise

        responseLogDict['size'] = sizeInBytes
        if httpStatus:
            responseLogDict['httpStatus'] = httpStatus
        responseLogDict['duration'] = self._time() - timestamp
        collectLogForScope(httpRequest=requestLogDict, httpResponse=responseLogDict)

    def logHttpError(self, ResponseCode=None, **kwargs):
        requestLogDict = dict()
        responseLogDict = dict()
        requestLogDict['timestamp'] = self._time()
        for key in ['Client', 'Headers', 'RequestURI', 'Method', 'HTTPVersion']:
            if key in kwargs:
                requestLogDict[key] = kwargs[key]
        if ResponseCode:
            responseLogDict['httpStatus'] = str(ResponseCode)
        self.do.logHttpError(ResponseCode=ResponseCode, **kwargs)
        collectLogForScope(httpRequest=requestLogDict, httpResponse=responseLogDict)

    def _time(self):
        return time()
