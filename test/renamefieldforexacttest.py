## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from unittest import TestCase

from cqlparser import cql2string, parseString
from meresco.components import CqlMultiSearchClauseConversion, RenameFieldForExact


class RenameFieldForExactTest(TestCase):
    def testNothingToBeDone(self):
        self.assertEqual('field=value', self.convert('field=value'))

    def testRenameField(self):
        self.assertEqual('untokenized.field exact value', self.convert('field exact value'))

    def testDoNotRenameField(self):
        self.assertEqual('otherfield exact value', self.convert('otherfield exact value'))

    def testRenameFieldThatMatchesPrefix(self):
        self.assertEqual('untokenized.prefix.certainfield exact value', self.convert('prefix.certainfield exact value'))

    def convert(self, cqlString):
        converter = CqlMultiSearchClauseConversion([
                RenameFieldForExact(['untokenized.field', 'untokenized.prefix.*'], 'untokenized.').filterAndModifier()
            ], fromKwarg="cqlAbstractSyntaxTree")
        return cql2string(converter._convert(parseString(cqlString)))

