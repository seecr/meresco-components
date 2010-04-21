## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
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
from cqlparser import parseString
from merescocomponents.facetindex import LuceneIndex, Document, CQL2LuceneQuery
from meresco.components.numeric.numbercomparitorfieldlet import NumberComparitorFieldlet
from meresco.components.numeric import NumberComparitorCqlConversion
from meresco.components.numeric.convert import Convert
from meresco.core import be, Observable

unqualifiedTermFields = [('field',1.0)]

class NumberComparitorTest(CQ2TestCase):
    def setUpIndex(self, values, nrOfDecimals, valueLength):
        self.index = LuceneIndex(self.tempdir)
        self.nrOfDecimals = nrOfDecimals
        self.valueLength = valueLength

        observer = CallTrace('observer')
        fieldlet = NumberComparitorFieldlet(nrOfDecimals=nrOfDecimals, valueLength=valueLength)
        fieldlet.addObserver(observer)

        def addValue(rating):
            doc = Document(rating)
            def addField(name, value):
                doc.addIndexedField(name, value)
            observer.addField = addField
            fieldlet.addField('field', rating)
            self.index.addDocument(doc)

        for value in values:
            addValue(value)
        self.index.commit()


    def assertResult(self, expectedResult, query):
        dna = be((Observable(),
            (NumberComparitorCqlConversion('field', self.nrOfDecimals, valueLength=self.valueLength),
                (CQL2LuceneQuery(unqualifiedTermFields),
                    (self.index,)
                )
            )
        ))
        total, recordIds = dna.any.executeCQL(cqlAbstractSyntaxTree=parseString(query))
        self.assertEquals(expectedResult, sorted(recordIds))
        
    def testGTE_1_Decimal(self):
        self.setUpIndex(['1.0', '1.9', '2.0', '2.3', '5.0'], nrOfDecimals=1, valueLength=2)

        self.assertResult(['1.0', '1.9', '2.0', '2.3', '5.0'], 'field >= 0.0')
        self.assertResult(['1.0', '1.9', '2.0', '2.3', '5.0'], 'field >= 1.0')
        self.assertResult(['1.9', '2.0', '2.3', '5.0'], 'field >= 1.9')
        self.assertResult(['2.0', '2.3', '5.0'], 'field >= 2.0')
        self.assertResult(['2.3', '5.0'], 'field >= 2.2')
        self.assertResult(['2.3', '5.0'], 'field >= 2.3')
        self.assertResult(['5.0'], 'field >= 2.4')
        self.assertResult(['5.0'], 'field >= 3.0')
        self.assertResult(['5.0'], 'field >= 3.1')
        self.assertResult(['5.0'], 'field >= 5.0')
        self.assertResult([], 'field >= 6.0')

    def testGT_1_Decimal(self):
        self.setUpIndex(['1.0', '1.9', '2.0', '2.3', '5.0'],
            nrOfDecimals=1, valueLength=2)

        self.assertResult(['1.0', '1.9', '2.0', '2.3', '5.0'], 'field > 0.0')
        self.assertResult(['1.9', '2.0', '2.3', '5.0'], 'field > 1.0')
        self.assertResult(['2.0', '2.3', '5.0'], 'field > 1.9')
        self.assertResult(['2.3', '5.0'], 'field > 2.0')
        self.assertResult(['2.3', '5.0'], 'field > 2.2')
        self.assertResult(['5.0'], 'field > 2.3')
        self.assertResult(['5.0'], 'field > 2.4')
        self.assertResult(['5.0'], 'field > 3.0')
        self.assertResult(['5.0'], 'field > 3.1')
        self.assertResult([], 'field > 5.0')
        self.assertResult([], 'field > 6.0')
        self.assertResult([], 'field > 19.0')

    def testLTE_1_Decimal(self):
        self.setUpIndex(['1.0', '1.9', '2.0', '2.3', '5.0'],
            nrOfDecimals=1, valueLength=2)

        self.assertResult([], 'field <= 0.0')
        self.assertResult(['1.0'], 'field <= 1.0')
        self.assertResult(['1.0', '1.9'], 'field <= 1.9')
        self.assertResult(['1.0', '1.9', '2.0'], 'field <= 2.0')
        self.assertResult(['1.0', '1.9', '2.0'], 'field <= 2.2')
        self.assertResult(['1.0', '1.9', '2.0', '2.3'], 'field <= 2.3')
        self.assertResult(['1.0', '1.9', '2.0', '2.3'], 'field <= 2.4')
        self.assertResult(['1.0', '1.9', '2.0', '2.3'], 'field <= 3.0')
        self.assertResult(['1.0', '1.9', '2.0', '2.3'], 'field <= 3.1')
        self.assertResult(['1.0', '1.9', '2.0', '2.3', '5.0'], 'field <= 5.0')
        self.assertResult(['1.0', '1.9', '2.0', '2.3', '5.0'], 'field <= 6.0')

    def testLT_1_Decimal(self):
        self.setUpIndex(['1.0', '1.9', '2.0', '2.3', '5.0'],
            nrOfDecimals=1, valueLength=2)

        self.assertResult([], 'field < 0.0')
        self.assertResult([], 'field < 1.0')
        self.assertResult(['1.0'], 'field < 1.9')
        self.assertResult(['1.0', '1.9'], 'field < 2.0')
        self.assertResult(['1.0', '1.9', '2.0'], 'field < 2.2')
        self.assertResult(['1.0', '1.9', '2.0'], 'field < 2.3')
        self.assertResult(['1.0', '1.9', '2.0', '2.3'], 'field < 2.4')
        self.assertResult(['1.0', '1.9', '2.0', '2.3'], 'field < 3.0')
        self.assertResult(['1.0', '1.9', '2.0', '2.3'], 'field < 3.1')
        self.assertResult(['1.0', '1.9', '2.0', '2.3'], 'field < 5.0')
        self.assertResult(['1.0', '1.9', '2.0', '2.3', '5.0'], 'field < 6.0')

    def testBiggerRange(self):
        self.setUpIndex(['1', '350', '351', '800', '999'],
            nrOfDecimals=0, valueLength=3)

        self.assertResult(['1','350','351','800','999'], 'field > 0')
        self.assertResult(['1','350','351','800','999'], 'field >= 1')
        self.assertResult(['350','351','800','999'], 'field > 1')
        self.assertResult(['350','351','800','999'], 'field > 349')
        self.assertResult(['350','351','800','999'], 'field >= 350')
        self.assertResult(['351','800','999'], 'field > 350')
        self.assertResult(['999'], 'field > 998')
        self.assertResult([], 'field > 1234')
        self.assertResult(['1','350','351','800','999'], 'field <= 1234')
        self.assertResult(['1','350','351','800','999'], 'field <= 999')
        self.assertResult(['1','350','351','800'], 'field < 999')
        self.assertResult(['1','350','351'], 'field <= 351')
        self.assertResult(['1','350'], 'field < 351')
        self.assertResult([], 'field < 1')
        self.assertResult([], 'field < -3456')

    def testHugeRange(self):
        self.setUpIndex(['1', '1234567', '%s' % (9 * (10**11))],
            nrOfDecimals=0, valueLength=12)

        self.assertResult(['1234567', '900000000000'], 'field > 2')
        

