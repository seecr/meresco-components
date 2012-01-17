## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from seecr.test import SeecrTestCase, CallTrace

from meresco.core import Observable

from weightless.core import be

from string import punctuation

from meresco.components.tokenizefieldlet import TokenizeFieldlet

class Tokens(object):
    def __init__(self):
        self.tokens = []
    def addField(self, field, value):
        self.tokens.append(value)

class TokenizeFieldletTest(SeecrTestCase):

    def assertTokenized(self, expected, value):
        tokens = Tokens()
        dna = be(
            (Observable(),
                (TokenizeFieldlet(),
                    (tokens, )
                )
            )
        )
        dna.do.addField('name', value)
        self.assertEquals(expected, tokens.tokens)

    def testOne(self):
        self.assertTokenized(['value'], 'value')
        self.assertTokenized(['value1', 'value2'], 'value1 value2')

    def testDitchQuotes(self):
        self.assertTokenized(['value'], '"value"')
        self.assertTokenized(['jan', 'janssen'], '"jan janssen"')
        self.assertTokenized(['mozes', "ma'an"], """'mozes ma'an'""")
        self.assertTokenized(['ga'], "a , f ga ! b?")

    def testLower(self):
        self.assertTokenized(['value'], '"ValUe"')

    def testIgnore(self):
        self.assertTokenized(['aap', '43', 'mies'], ' 9 aap 43 mies')
