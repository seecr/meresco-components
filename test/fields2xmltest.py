## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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

from meresco.components import Fields2XmlTx
from meresco.components.fields2xml import Fields2XmlException, generateXml
from amara.binderytools import bind_string

class Fields2XmlTest(CQ2TestCase):
    def testOne(self):
        transaction = CallTrace('Transaction')
        ctx = CallTrace('CTX')
        tx = CallTrace('TX')
        tx.locals = {'id': 'identifier'}
        transaction.ctx = ctx
        transaction.ctx.tx = tx
        transactionDo = CallTrace('TransactionDo')
        transaction.do = transactionDo
        
        f = Fields2XmlTx(transaction, 'extra')

        f.addField('key.sub', 'value')
        f.commit()

        self.assertEquals(['store'], [m.name for m in transactionDo.calledMethods])
        self.assertEquals(('identifier', 'extra', '<extra><key><sub>value</sub></key></extra>'), transactionDo.calledMethods[0].args)

    def testPartNameIsDefinedAtInitialization(self):
        transaction = CallTrace('Transaction')
        ctx = CallTrace('CTX')        
        tx = CallTrace('TX')
        tx.locals = {'id': 'otherIdentifier'}
        transaction.ctx = ctx
        transaction.ctx.tx = tx
        transactionDo = CallTrace('TransactionDo')
        transaction.do = transactionDo
        
        f = Fields2XmlTx(transaction, 'partName')
        f.addField('key.sub', 'value')
        f.commit()
        
        self.assertEquals('otherIdentifier', transactionDo.calledMethods[0].args[0])
        self.assertEquals('partName', transactionDo.calledMethods[0].args[1])
        xml = bind_string(transactionDo.calledMethods[0].args[2])
        self.assertEquals('partName', str(xml.childNodes[0].localName))

    def testNamespace(self):
        transaction = CallTrace('Transaction')
        ctx = CallTrace('CTX')         
        tx = CallTrace('TX')
        tx.locals = {'id': 'identifier'}
        transaction.ctx = ctx
        transaction.ctx.tx = tx  
        transactionDo = CallTrace('TransactionDo')
        transaction.do = transactionDo
        
        f = Fields2XmlTx(transaction, 'extra', namespace="http://meresco.org/namespace/fields/extra")
        f.addField('key.sub', 'value')
        f.commit()
        
        self.assertEquals(('identifier', 'extra', '<extra xmlns="http://meresco.org/namespace/fields/extra"><key><sub>value</sub></key></extra>'), transactionDo.calledMethods[0].args)

    def testIllegalPartNameRaisesException(self):
        for name in ['this is wrong', '%%@$%*^$^', '/slash', 'dot.dot']:
            try:
                Fields2XmlTx('ignored', name)
                self.fail('Expected error for ' + name)
            except Fields2XmlException, e:
                self.assertTrue(name in str(e))

    def testGenerateOneKeyXml(self):
        self.assertEquals('<key>value</key>', generateXml([('key','value')]))

    def testGenerateOneSubKeyXml(self):
        self.assertEquals('<key><sub>value</sub></key>', generateXml([('key.sub','value')]))
   
    def testGenerateTwoSubKeyXml(self):
        self.assertEquals('<key><sub>value</sub><sub2>value2</sub2></key>', generateXml([('key.sub','value'), ('key.sub2','value2')]))

    def testGenerateOtherParentKeyXml(self):
        self.assertEquals('<a><b>value</b></a><c><d>value2</d></c>', generateXml([('a.b','value'), ('c.d','value2')]))

    def testGenerateXml(self):
        self.assertEquals('<a><b><c><d>DDD</d><e>EEE</e></c><c>CCC</c><f>FFF</f><c><d>DDD</d></c></b></a>', generateXml([('a.b.c.d','DDD'), ('a.b.c.e','EEE'), ('a.b.c', 'CCC'),('a.b.f', 'FFF'), ('a.b.c.d', 'DDD')]))

    def testEscapeTagNamesAndValues(self):
        try:
            generateXml([('k/\\.sub','value')])
            self.fail()
        except Fields2XmlException, e:
            self.assertTrue('k/\\.sub' in str(e))


        self.assertEquals('<key>&lt;/tag&gt;</key>', generateXml([('key','</tag>')]))
        
