## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2021 Seecr (Seek You Too B.V.) https://seecr.nl
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
from os.path import splitext, isfile, dirname
from seecr.zulutime import ZuluTime
from hashlib import md5
from os import stat
from magic import Magic

from meresco.components import DirectoryWatcher

class StaticFileMapping(Observable):
    def __init__(self, mapping, reactor=None, **kwargs):
        Observable.__init__(self, **kwargs)
        self._mapping = {}
        self._watchers = {}
        self._reactor = reactor
        self._magic = Magic(mime=True)
        for shortname, filename in mapping.items():
            if not isfile(filename):
                print(f"file {filename} for {shortname} does not exist.")
                del self._mapping[shortname]
            else:
                if not self._reactor is None:
                    basedir = dirname(filename)
                    if not basedir in self._watchers:
                        self._watchers[basedir] = DirectoryWatcher(basedir, self._update, ModifyFile=True, MoveInFile=True)
                self._updateFile(shortname, filename)

        if not self._reactor is None:
            for each in self._watchers.values():
                self._reactor.addReader(each, each)

    def _update(self, event, *args, **kwargs):
        for shortname, values in self._mapping.items():
            filename = values['filename']
            if filename == event.pathname:
                self._updateFile(shortname, filename)
                break

    def _updateFile(self, shortname, filename):
        with open(filename, 'rb') as fp:
            etag = md5(fp.read()).hexdigest()
        self._mapping[shortname] = dict(
            filename=filename,
            etag=etag,
            lastModified=ZuluTime(stat(filename).st_mtime).rfc1123(),
        )

    def paths(self):
        return list(self._mapping.keys())

    def handleRequest(self, path, Headers, **kwargs):
        if path in self._mapping:
            item = self._mapping[path]
            defaultHeaders = [
                "Date: {}\r\n".format(ZuluTime().rfc1123()),
                'etag: {}\r\n'.format(item['etag']),
                'Last-Modified: {}\r\n'.format(item['lastModified'])
            ]
            for key in Headers:
                if key.lower() == 'etag' and Headers[key] == item['etag']:
                    yield "HTTP/1.0 304 Not Modified\r\n"
                    for each in defaultHeaders:
                        yield each
                    yield "\r\n"
                    return

            filename = self._mapping[path]['filename']
            _, ext = splitext(filename)
            yield 'HTTP/1.0 200 OK\r\n'
            yield 'Content-type: {}\r\n'.format(self._magic.from_file(filename))
            for each in defaultHeaders:
                yield each
            yield '\r\n'
            with open(filename, "rb") as fp:
                yield fp.read()
