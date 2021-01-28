## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010-2011, 2015, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012, 2015, 2017, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2017 SURFmarket https://surf.nl
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

from seecr.test import SeecrTestCase, CallTrace
from meresco.components import CqlSearchClauseConversion, CqlMultiSearchClauseConversion
from meresco.core import Observable
from weightless.core import be, consume
from cqlparser import cqlToExpression


class CQLConversionTest(SeecrTestCase):

    def testSearchClauseNoModification(self):
        query = cqlToExpression('field=value')
        modifier = CallTrace('SearchClauseModifier')
        conversion = CqlSearchClauseConversion(lambda query: False, modifier.modify, fromKwarg="aQuery")

        observer = CallTrace('observer')
        o = be((Observable(),
            (conversion,
                (observer,)
            )
        ))
        o.do.whatever(aQuery=query)

        self.assertEqual(1, len(observer.calledMethods))
        self.assertEqual('whatever', observer.calledMethods[0].name)
        self.assertEqual({'aQuery': query}, observer.calledMethods[0].kwargs)

    def testSearchClauseModifySimpleSearchClause(self):
        query = cqlToExpression('field=value')
        def canModify(expression):
            return True
        def modify(expression):
            expression.index = 'otherfield'
            expression.term = 'othervalue'
        conversion = CqlSearchClauseConversion(canModify, modify, fromKwarg="aQuery")
        result = conversion._convert(query)
        self.assertEqual(cqlToExpression('otherfield = othervalue'), result)

    def testMultipleSearchClauseReplacements(self):
        ast = cqlToExpression('term1 AND term2 AND term3')
        #SEARCH_TERM(TERM('term'))
        def canModifyTerm1(expression):
            return expression.term == 'term1'
        def modifyTerm1(expression):
            expression.term = 'termOne'
        def canModifyTerm3(expression):
            return expression.term == 'term3'
        def modifyTerm3(expression):
            expression.term = 'termThree'
        observerClassic = CallTrace('observerClassic')
        observerNewStyle = CallTrace('observerNewStyle')
        classic = be((Observable(),
            (CqlSearchClauseConversion(canModifyTerm1, modifyTerm1, fromKwarg="thisQuery"),
                (CqlSearchClauseConversion(canModifyTerm3, modifyTerm3, fromKwarg="thisQuery"),
                    (observerClassic,)
                )
            )
        ))
        newStyle = be((Observable(),
            (CqlMultiSearchClauseConversion([
                    (canModifyTerm1, modifyTerm1),
                    (canModifyTerm3, modifyTerm3)
                ], fromKwarg="thisQuery"),
                (observerNewStyle,)
            )
        ))

        classic.do.message(thisQuery=ast)
        newStyle.do.message(thisQuery=ast)

        self.assertEqual(['message'], [m.name for m in observerClassic.calledMethods])
        resultClassic = observerClassic.calledMethods[0].kwargs['thisQuery']
        self.assertEqual(['message'], [m.name for m in observerNewStyle.calledMethods])
        resultNewStyle = observerNewStyle.calledMethods[0].kwargs['thisQuery']

        self.assertEqual(cqlToExpression('termOne AND term2 AND termThree'), resultClassic)
        self.assertEqual(cqlToExpression('termOne AND term2 AND termThree'), resultNewStyle)

    def testNestedWithReplaced(self):
        q = cqlToExpression('A')
        def canModify1(expression):
            return expression.term == 'A'
        def modify1(expression):
            expression.replaceWith(cqlToExpression('aa OR bb'))
        def canModify2(expression):
            return expression.term == 'bb'
        def modify2(expression):
            expression.term = 'B'
        conversion = CqlMultiSearchClauseConversion([
                    (canModify1, modify1),
                    (canModify2, modify2),
                ], fromKwarg="thisQuery")
        result = conversion._convert(q)
        self.assertEqual(cqlToExpression('aa OR B'), result)

    def testIgnoreOtherMethodsWithQueryArgument(self):
        def canModify(expression):
            return expression.term == 'term'
        def modify(expression):
            expression.term = 'changed'
        observer = CallTrace(emptyGeneratorMethods=['method'])
        top = be((Observable(),
            (CqlMultiSearchClauseConversion([(canModify, modify)], fromKwarg='query'),
                (observer,)
            )
        ))
        consume(top.any.method(query='index = term'))
        self.assertEqual({'query': 'index = term'}, observer.calledMethods[0].kwargs)
        observer.calledMethods.reset()
        consume(top.any.method(query=cqlToExpression('index = term')))
        self.assertEqual({'query': cqlToExpression('index = changed')}, observer.calledMethods[0].kwargs)

