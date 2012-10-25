## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
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
from StringIO import StringIO

from meresco.components import IteratorAsStream

class IteratorAsStreamTest(SeecrTestCase):
    def testEmptyIterator(self):
        stream = IteratorAsStream(iter([]))
        self.assertEquals('', stream.read())

    def testReadWithSize(self):
        def assertStream1(stream):
            self.assertEquals("12345", stream.read(5))
            self.assertEquals("67890", stream.read(42))
            self.assertEquals('', stream.read())
            self.assertEquals('', stream.read())
        def assertStream2(stream):
            self.assertEquals("12345", stream.read(5))
            self.assertEquals("", stream.read(0))
            self.assertEquals("67890", stream.read(-1))
            self.assertEquals('', stream.read())
        def assertStream3(stream):
            self.assertEquals("12345", stream.read(5))
            self.assertEquals("67890", stream.read())
            self.assertEquals('', stream.read())
        def assertStream4(stream):
            self.assertEquals("1234567890", stream.read(-19))
        def assertStream5(stream):
            self.assertEquals("1234567890", stream.read())

        assertStream1(StringIO("1234567890"))
        assertStream2(StringIO("1234567890"))
        assertStream3(StringIO("1234567890"))
        assertStream4(StringIO("1234567890"))
        assertStream5(StringIO("1234567890"))

        assertStream1(IteratorAsStream("1234567890"))
        assertStream2(IteratorAsStream("1234567890"))
        assertStream3(IteratorAsStream("1234567890"))
        assertStream4(IteratorAsStream("1234567890"))
        assertStream5(IteratorAsStream("1234567890"))

        assertStream1(IteratorAsStream(iter("1234567890")))
        assertStream2(IteratorAsStream(iter("1234567890")))
        assertStream3(IteratorAsStream(iter("1234567890")))
        assertStream4(IteratorAsStream(iter("1234567890")))
        assertStream5(IteratorAsStream(iter("1234567890")))
        
        assertStream1(IteratorAsStream((f for f in ["123","456","78","90"])))
        assertStream2(IteratorAsStream((f for f in ["123","456","78","90"])))
        assertStream3(IteratorAsStream((f for f in ["123","456","78","90"])))
        assertStream4(IteratorAsStream((f for f in ["123","456","78","90"])))
        assertStream5(IteratorAsStream((f for f in ["123","456","78","90"])))


    def testStreamAsIterator(self):
        stream = IteratorAsStream((f for f in ["123","456","78","90"]))

        self.assertEquals("123", stream.next())
        self.assertEquals("45", stream.read(2))
        self.assertEquals("6", stream.next())
        self.assertEquals("78", stream.next())
        self.assertEquals("90", stream.next())
        self.assertRaises(StopIteration, stream.next)

        stream = IteratorAsStream((f for f in ["123","456","78","90"]))
        self.assertEquals(["123","456","78","90"], [f for f in stream])
        stream = IteratorAsStream((f for f in ["123","456","78","90"]))
        self.assertEquals("123, 456, 78, 90", ', '.join(stream))

        stream = IteratorAsStream((f for f in ["123","456","78","90"]))
        stream.read()
        self.assertRaises(StopIteration, stream.next)

        stream = IteratorAsStream((f for f in []))
        self.assertRaises(StopIteration, stream.next)
