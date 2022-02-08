## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012-2015, 2020, 2022 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2014, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from os import rename
import pathlib, simplejson as json


class _Json(object):
    def dumps(self, *args, **kwargs):
        return json.dumps(self, *args, **kwargs)
    __str__ = dumps

    def pretty_print(self, indent=4):
        return json.dumps(self, indent=indent, sort_keys=True)

    def dump(self, fp, *args, **kwargs):
        if hasattr(fp, 'write'):
            json.dump(self, fp, *args, **kwargs)
        else:
            fp = pathlib.Path(fp)
            tmp = fp.with_name(fp.name + '~')
            tmp.write_text(json.dumps(self, *args, **kwargs))
            tmp.rename(fp)

    @classmethod
    def loads(clz, s, *args, **kwargs):
        return clz(json.loads(s, *args, **kwargs))

    @classmethod
    def load(clz, fp, emptyOnError=False, *args, **kwargs):
        def _inner(clz, fp, emptyOnError=False, *args, **kwargs):
            try:
                return clz(json.load(fp, *args, **kwargs))
            except json.JSONDecodeError:
                if emptyOnError:
                    return clz()
                raise
        if not hasattr(fp, 'read'):
            with open(fp) as fp:
                return _inner(clz, fp, emptyOnError=emptyOnError, *args, **kwargs)
        else:
            return _inner(clz, fp, emptyOnError=emptyOnError, *args, **kwargs)

class JsonDict(dict, _Json):
    pass

class JsonList(list, _Json):
    pass

__all__ = ["JsonDict", "JsonList"]

