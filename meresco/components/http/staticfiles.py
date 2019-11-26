## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2016-2017, 2019 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2017 SURF http://www.surf.nl
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

from weightless.core import be
from fileserver import FileServer
from pathrename import PathRename
from pathfilter import PathFilter
from os.path import join, isdir
from os import listdir

class StaticFiles(object):
    def __init__(self, libdir, path, allowDirectoryListing=False):
        self.path = path
        if not self.path.endswith('/'):
            self.path += '/'
        self._top = be((PathFilter(self.path),
            (PathRename(lambda path:path[len(self.path):] or '/'),
                (FileServer(libdir, allowDirectoryListing=allowDirectoryListing, basePath=self.path),)
            )
        ))

    def handleRequest(self, **kwargs):
        yield self._top.handleRequest(**kwargs)

def libdirForPrefix(basedir, prefix):
    matches = [d for d in listdir(basedir) if d.startswith(prefix) and isdir(join(basedir, d))]
    if len(matches) == 1:
        return join(basedir, matches[0])
    errormessage = 'No match found for {} in {}' if len(matches) == 0 else 'Too many matches found for {} in {}'
    raise ValueError(errormessage.format(repr(prefix), repr(basedir)))
