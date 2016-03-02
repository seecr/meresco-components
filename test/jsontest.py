## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015-2016 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from os.path import join

from seecr.test import SeecrTestCase

from meresco.components.json import JsonDict, JsonList
from simplejson import JSONDecodeError

class JsonTest(SeecrTestCase):
    def testStr(self):
        jd = JsonDict({'hello': 'world'})
        self.assertEqual('{"hello": "world"}', str(jd))

    def testPrettyPrint(self):
        jd = JsonDict({'hello': 'world'})
        self.assertEqual('{\n     "hello": "world"\n}', jd.pretty_print(indent=5))

    def testLoads(self):
        jd = JsonDict({'hello': 'world'})
        jd2 = JsonDict.loads(str(jd))
        self.assertEqual(jd, jd2)

    def testLoad(self):
        jd = JsonDict({'hello': 'world'})
        tempfile = join(self.tempdir, 'json.json')
        with open(tempfile, "w") as fp:
            fp.write(str(jd))
        with open(tempfile) as fp:
            jd2 = JsonDict.load(fp)
        self.assertEqual(jd, jd2)

    def testLoadFromFilename(self):
        jd = JsonDict({'hello': 'world'})
        tempfile = join(self.tempdir, 'json.json')
        with open(tempfile, 'w') as fp:
            fp.write(str(jd))
        jd2 = JsonDict.load(tempfile)
        self.assertEqual(jd, jd2)

    def testDump(self):
        jd = JsonDict({'hello': 'world'})
        tempfile = join(self.tempdir, 'json.json')
        with open(tempfile, 'w') as f:
            jd.dump(f)
        with open(tempfile) as fp:
            self.assertEqual('{"hello": "world"}', fp.read())

    def testDumpWithFilename(self):
        jd = JsonDict({'hello': 'world'})
        tempfile = join(self.tempdir, 'json.json')
        jd.dump(tempfile)
        with open(tempfile) as fp:
            self.assertEqual('{"hello": "world"}', fp.read())

    def testStrList(self):
        jl = JsonList(['hello', 'world'])
        self.assertEqual('["hello", "world"]', str(jl))

    def testPrettyPrintList(self):
        jd = JsonList(['hello', 'world'])
        printedList = jd.pretty_print(indent=5)
        self.assertTrue('\n     "hello"' in printedList)
        self.assertTrue('\n     "world"' in printedList)

    def testLoadsList(self):
        jd = JsonList(['hello', 'world'])
        jd2 = JsonList.loads(str(jd))
        self.assertEqual(jd, jd2)

    def testLoadList(self):
        jd = JsonList(['hello', 'world'])
        tempfile = join(self.tempdir, 'json.json')
        with open(tempfile, 'w') as fp:
            fp.write(str(jd))
        with open(tempfile) as fp:
            jd2 = JsonList.load(fp)
        self.assertEqual(jd, jd2)

    def testLoadEmptyFile(self):
        tempfile = join(self.tempdir, 'json.json')
        open(tempfile, 'w').close()
        self.assertRaises(JSONDecodeError, lambda: JsonDict.load(tempfile))
        self.assertEqual({}, JsonDict.load(tempfile, emptyOnError=True))
        self.assertRaises(JSONDecodeError, lambda: JsonList.load(tempfile))
        self.assertEqual([], JsonList.load(tempfile, emptyOnError=True))
