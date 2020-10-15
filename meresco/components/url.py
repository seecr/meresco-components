## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015, 2019-2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from urllib.parse import urlsplit

def parseAbsoluteUrl(url):
    parsedUrl = urlsplit(url)
    host = parsedUrl.hostname
    scheme = parsedUrl.scheme
    if host is None:
        return None

    port = int(parsedUrl.port) if parsedUrl.port else {'https': 443, 'ftp': 21, 'http': 80}.get(parsedUrl.scheme, 80)
    return _dict(
        scheme=scheme,
        host=host,
        port=port,
        path=parsedUrl.path,
        query=parsedUrl.query,
        fragment=parsedUrl.fragment,
        username=parsedUrl.username,
        password=parsedUrl.password,
    )

class _dict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)
