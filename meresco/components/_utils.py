## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2018 Seecr (Seek You Too B.V.) http://seecr.nl
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

from contextlib import contextmanager
from os import rename

class Bucket(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def get(self, key, default):
        return self.__dict__.get(key, default)

    def __repr__(self):
        return simplerepr(self)

    def asDict(self):
        return dict(self.__dict__)


def simplerepr(o):
    return '%s(%s)' % (o.__class__.__name__, ', '.join("%s=%s" % (key, repr(value)) for key, value in o.__dict__.items()))

@contextmanager
def atomic_write(filename, mode="w", tmpPostfix=".tmp"):
    tmp_filename = "{}{}".format(filename, tmpPostfix)
    with open(tmp_filename, mode) as fp:
        yield fp
    rename(tmp_filename, filename)

__all__ = ['simplerepr', 'Bucket', 'atomic_write']
