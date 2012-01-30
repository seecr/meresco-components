## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.core import Observable
from warnings import warn

class Converter(Observable):
    def __init__(self, name=None, fromKwarg=None, toKwarg=None):
        Observable.__init__(self, name=name)
        if fromKwarg is None:
            warn("This use of %s is deprecated. Specify 'fromKwarg' and 'toKwarg' parameters to convert specific keyword argument." % self.__class__.__name__, DeprecationWarning)
        self._fromKwarg = fromKwarg
        self._toKwarg = toKwarg if toKwarg else self._fromKwarg

    def unknown(self, msg, *args, **kwargs):
        if self._fromKwarg is None:
            newArgs = [self._detectAndConvert(arg) for arg in args]
            newKwargs = dict((key, self._detectAndConvert(value)) for key, value in kwargs.items())
            return self.all.unknown(msg, *newArgs, **newKwargs)

        try:
            oldvalue = kwargs[self._fromKwarg]
        except KeyError:
            pass
        else:
            del kwargs[self._fromKwarg]
            kwargs[self._toKwarg] = self._convert(oldvalue)

        return self.all.unknown(msg, *args, **kwargs)

    def _convert(self, anObject):
        raise NotImplementedError()

    def _canConvert(self, anObject):
        "deprecated"
        raise NotImplementedError()

    def _detectAndConvert(self, anObject):
        "deprecated"
        if self._canConvert(anObject):
            return self._convert(anObject)
        return anObject


