## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  initiated by Stichting Bibliotheek.nl to provide a new search service
#  for all public libraries in the Netherlands.
#
# Copyright (C) 2012-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
#
# This file is part of "NBC+ (Zoekplatform BNL)"
#
# "NBC+ (Zoekplatform BNL)" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "NBC+ (Zoekplatform BNL)" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "NBC+ (Zoekplatform BNL)"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from os.path import join

from seecr.test import SeecrTestCase

from meresco.components.json import JsonDict, JsonList

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

