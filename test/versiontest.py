## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014-2016, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 Stichting Kennisnet https://www.kennisnet.nl
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


from seecr.test import SeecrTestCase

from meresco.components.version import Version

class VersionTest(SeecrTestCase):

    def testVersionX(self):
        self.assertTrue(Version.create('1.4') <= Version.create('1.4.x') < Version.create('1.5'))
        self.assertTrue(Version.create('1.4.3') <= Version.create('1.4.x') < Version.create('1.5'))
        self.assertRaises(Exception, lambda: Version.create('1.4.development'))

    def testVersionComparisons(self):
        self.assertTrue(Version.create('1.4') <= Version.create('1.4.3') < Version.create('1.5'))
        self.assertFalse(Version.create('1.4') <= Version.create('1.3') < Version.create('1.5'))
        self.assertFalse(Version.create('1.4') <= Version.create('1.42.3') < Version.create('1.5'))
        self.assertTrue(Version.create('1.4.2') <= Version.create('1.4.3') < Version.create('1.5'))
        self.assertFalse(Version.create('1.4.2') <= Version.create('1.4') < Version.create('1.5'))

    def testMajorVersion(self):
        self.assertEqual(Version.create('1.4'), Version.create('1.4').majorVersion())
        self.assertEqual(Version.create('1.4'), Version.create('1.4.x').majorVersion())
        self.assertEqual(Version.create('1.4'), Version.create('1.4.3.2').majorVersion())
        self.assertEqual(Version.create('1.0'), Version.create('1').majorVersion())

    def testNextMajorVersion(self):
        self.assertEqual(Version.create('1.5'), Version.create('1.4').nextMajorVersion())
        self.assertEqual(Version.create('1.5'), Version.create('1.4.x').nextMajorVersion())
        self.assertEqual(Version.create('1.5'), Version.create('1.4.3.2').nextMajorVersion())
        self.assertEqual(Version.create('1.55'), Version.create('1.54.3.2').nextMajorVersion())
        self.assertEqual(Version.create('1.1'), Version.create('1').nextMajorVersion())

    def testVersionAsString(self):
        self.assertEqual('1.4', '%s' % Version.create('1.4'))
        self.assertEqual('1.4', str(Version.create('1.4')))
        self.assertEqual('1.4', '{0}'.format(Version.create('1.4')))

    def testMajorVersionMoreDigits(self):
        self.assertEqual(Version("1.2.3"), Version("1.2.3.4.5", majorDigits=3).majorVersion())
        self.assertEqual(Version("1.2.4"), Version("1.2.3.4.5", majorDigits=3).nextMajorVersion())
        self.assertRaises(ValueError, lambda: Version("1.2.x", majorDigits=3).majorVersion())

    def testRepr(self):
        self.assertEqual("Version('1.4')", repr(Version.create('1.4')))

    def testHash(self):
        self.assertEqual(hash(Version.create('1.5')), hash(Version.create('1.5')))
        self.assertEqual('value', {Version.create('1.5'):'value'}[Version.create('1.5')])

    def testVersionVersion(self):
        self.assertEqual('1.4', '%s' % Version(Version.create('1.4')))

    def testVersionOfVersionIsSameInstance(self):
        v = Version.create('1.4')
        v2 = Version.create(v)
        self.assertEqual(v, v2)
        self.assertEqual(id(v), id(v2))

    def testMajorVersionIsSameInstance(self):
        v = Version.create('1.4')
        mv = v.majorVersion()
        nmv = v.nextMajorVersion()
        self.assertEqual('1.4', '%s' % mv)
        self.assertEqual('1.5', '%s' % nmv)
        self.assertEqual(id(mv), id(v.majorVersion()))
        self.assertEqual(id(nmv), id(v.nextMajorVersion()))
