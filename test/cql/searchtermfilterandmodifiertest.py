## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2011-2012, 2015, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from unittest import TestCase

from cqlparser import cqlToExpression
from meresco.components import CqlMultiSearchClauseConversion

from meresco.components.cql import SearchTermFilterAndModifier

class SearchTermFilterAndModifierTest(TestCase):
    def testModifyValue(self):
        self.assertEqual(
            cqlToExpression('afield exact newvalue'),
            self.convert(
                cql='afield exact Pvalue',
                shouldModifyFieldValue=lambda name, relation, value: name=='afield' and relation=='exact' and value.startswith('P'),
                valueModifier=lambda value: 'newvalue'))

        self.assertEqual(
            cqlToExpression('afield=newvalue'),
            self.convert(
                cql='afield=Pvalue',
                shouldModifyFieldValue=lambda name, relation, value: value.startswith('P') and relation=='=',
                valueModifier=lambda value: 'newvalue'))

    def testNothingToBeDone(self):
        self.assertEqual(
            cqlToExpression('field exact value'),
            self.convert(
                cql='field exact value',
                shouldModifyFieldValue=lambda name, relation, value: name=='afield' and value.startswith('P'),
                valueModifier=lambda value: 'newvalue'))

        self.assertEqual(
            cqlToExpression('afield exact value'),
            self.convert(
                cql='afield exact value',
                shouldModifyFieldValue=lambda name, relation, value: name=='afield' and value.startswith('P'),
                valueModifier=lambda value: 'newvalue',
                fieldnameModifier=lambda field: 'newfield'))

        self.assertEqual(
            cqlToExpression('afield=Pvalue'),
            self.convert(
                cql='afield=Pvalue',
                shouldModifyFieldValue=lambda name, relation, value: name=='afield' and relation=='exact' and value.startswith('P'),
                valueModifier=lambda value: 'newvalue'))

    def testModifyField(self):
        self.assertEqual(
            cqlToExpression('newfield exact Pvalue'),
            self.convert(
                cql='afield exact Pvalue',
                shouldModifyFieldValue=lambda name, relation, value: name=='afield' and relation=='exact' and value.startswith('P'),
                fieldnameModifier=lambda value: 'newfield'))

        self.assertEqual(
            cqlToExpression('newfield=newvalue'),
            self.convert(
                cql='somefield=Pvalue',
                shouldModifyFieldValue=lambda name, relation, value: value.startswith('P') and relation=='=',
                valueModifier=lambda value: 'newvalue',
                fieldnameModifier=lambda field: 'newfield'))


    def convert(self, cql, shouldModifyFieldValue, valueModifier=None, fieldnameModifier=None):
        converter = CqlMultiSearchClauseConversion([
            SearchTermFilterAndModifier(
                shouldModifyFieldValue=shouldModifyFieldValue,
                valueModifier=valueModifier,
                fieldnameModifier=fieldnameModifier).filterAndModifier(),
            ], fromKwarg="aKwarg")
        return converter._convert(cqlToExpression(cql))

