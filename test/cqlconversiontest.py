## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from cq2utils import CQ2TestCase, CallTrace
from meresco.components import CQLConversion, CqlSearchClauseConversion, CqlMultiSearchClauseConversion
from meresco.core import Observable, be
from cqlparser import parseString, cql2string
from cqlparser.cqlparser import SEARCH_TERM, SEARCH_CLAUSE, TERM


class CQLConversionTest(CQ2TestCase):
    
    def testCQLContextSetConversion(self):
        observer = CallTrace('observer')
        o = be((Observable(),
            (CQLConversion(lambda ast:parseString('anotherQuery')),
                (observer,)
            )
        ))
        o.do.whatever(parseString('afield = value'))
        self.assertEquals(1, len(observer.calledMethods))
        self.assertEquals('whatever', observer.calledMethods[0].name)
        self.assertEquals((parseString('anotherQuery'),), observer.calledMethods[0].args)

    def testCQLCanConvert(self):
        c = CQLConversion(lambda ast: ast)
        self.assertTrue(c._canConvert(parseString('field = value')))
        self.assertFalse(c._canConvert('other object'))

    def testCQLConvert(self):
        converter = CallTrace('Converter')
        converter.returnValues['convert'] = parseString('ast')
        c = CQLConversion(converter.convert)
        self.assertEquals(parseString('ast'), c._convert(parseString('otherfield = value')))
        self.assertEquals(['convert'], [m.name for m in converter.calledMethods])

    def testSearchClauseNoModification(self):
        ast = parseString('field=value')
        modifier = CallTrace('SearchClauseModifier')
        conversion = CqlSearchClauseConversion(lambda node: False, modifier.modify)
        result = conversion._detectAndConvert(ast)
        self.assertEquals('field=value', cql2string(result))
        self.assertEquals(0, len(modifier.calledMethods))

    def testSearchClauseModifySimpleSearchClause(self):
        ast = parseString('field=value')
        def canModify(node):
            self.assertEquals(['INDEX', 'RELATION', 'SEARCH_TERM'], [c.name() for c in node.children()])
            return True
        def modify(node):
            return SEARCH_CLAUSE(SEARCH_TERM(TERM('newvalue')))
        conversion = CqlSearchClauseConversion(canModify, modify)
        result = conversion._detectAndConvert(ast)
        self.assertEquals('newvalue', cql2string(result))

    def testReplaceSubtree(self):
        ast = parseString('field1=value1 AND (field2=value2 OR (field3=value3))')
        def canModify(node):
            return ['CQL_QUERY'] == [c.name() for c in node.children()]
        def modify(node):
            return SEARCH_CLAUSE(SEARCH_TERM(TERM('newvalue')))
        conversion = CqlSearchClauseConversion(canModify, modify)
        result = conversion._detectAndConvert(ast)
        self.assertEquals('field1=value1 AND newvalue', cql2string(result))

    def testReplacementMustBeSearchClause(self):
        ast = parseString('term')
        canModify = lambda node: True
        modify = lambda node: TERM('wrong')
        conversion = CqlSearchClauseConversion(canModify, modify)
        self.assertRaises(AssertionError, conversion._detectAndConvert, ast)

    def testMultipleSearchClauseReplacements(self):
        ast = parseString('term1 AND term2 AND term3')
        #SEARCH_TERM(TERM('term'))
        def canModifyTerm1(node):
            return "SEARCH_CLAUSE(SEARCH_TERM(TERM('term1')))" == str(node)
        def modifyTerm1(node):
            return SEARCH_CLAUSE(SEARCH_TERM(TERM('termOne')))
        def canModifyTerm3(node):
            return "SEARCH_CLAUSE(SEARCH_TERM(TERM('term3')))" == str(node)
        def modifyTerm3(node):
            return SEARCH_CLAUSE(SEARCH_TERM(TERM('termThree')))
        observerClassic = CallTrace('observerClassic')
        observerNewStyle = CallTrace('observerNewStyle')
        classic = be((Observable(),
            (CqlSearchClauseConversion(canModifyTerm1,modifyTerm1),
                (CqlSearchClauseConversion(canModifyTerm3,modifyTerm3),
                    (observerClassic,)
                )
            )
        ))
        newStyle = be((Observable(),
            (CqlMultiSearchClauseConversion([
                    (canModifyTerm1, modifyTerm1),
                    (canModifyTerm3, modifyTerm3)
                ]),
                (observerNewStyle,)
            )
        ))

        classic.do.message(ast)
        newStyle.do.message(ast)

        self.assertEquals(['message'], [m.name for m in observerClassic.calledMethods])
        resultClassic = observerClassic.calledMethods[0].args[0]
        self.assertEquals(['message'], [m.name for m in observerNewStyle.calledMethods])
        resultNewStyle = observerNewStyle.calledMethods[0].args[0]

        self.assertEquals('termOne AND term2 AND termThree', cql2string(resultClassic))
        self.assertEquals('termOne AND term2 AND termThree', cql2string(resultNewStyle))




