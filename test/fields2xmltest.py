## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.components import Fields2Xml
from meresco.components.fields2xml import Fields2XmlException, generateXml
from meresco.core import Observable, TransactionScope, ResourceManager
from weightless.core import be, compose
from amara.binderytools import bind_string
from StringIO import StringIO
from lxml.etree import parse

class Fields2XmlTest(SeecrTestCase):
    def testOne(self):
        __callstack_var_tx__ = CallTrace('TX')
        __callstack_var_tx__.locals = {'id': 'identifier'}

        intercept = CallTrace()
        fields2Xml = Fields2Xml('extra')
        fields2Xml.addObserver(intercept)
        def f():
            f = yield fields2Xml.beginTransaction()
            yield f
        f = compose(f()).next()
        f.addField('key.sub', 'value')
        list(compose(f.commit()))

        self.assertEquals(['add'], [m.name for m in intercept.calledMethods])
        self.assertEquals(dict(identifier='identifier', partname='extra', data='<extra><key><sub>value</sub></key></extra>'), intercept.calledMethods[0].kwargs)

    def testAddNotCalledWhenNoAddFields(self):
        intercept = CallTrace()
        fields2Xml = Fields2Xml('extra')
        fields2Xml.addObserver(intercept)
        def f():
            f = yield fields2Xml.beginTransaction()
            yield f
        f = compose(f()).next()
        f.commit()

        self.assertEquals([], [m.name for m in intercept.calledMethods])
    
    def testSameAddFieldGeneratedTwoTimes(self):
        __callstack_var_tx__ = CallTrace('TX')
        __callstack_var_tx__.locals = {'id': 'identifier'}
        intercept = CallTrace()
        fields2Xml = Fields2Xml('extra')
        fields2Xml.addObserver(intercept)
        def f():
            f = yield fields2Xml.beginTransaction()
            yield f
        f = compose(f()).next()
        f.addField('key.sub', 'value')
        f.addField('key.sub', 'othervalue')
        f.addField('key.sub', 'value')
        f.addField('key.sub', 'separatedbyvalue')
        list(compose(f.commit()))

        self.assertEquals(['add'], [m.name for m in intercept.calledMethods])
        self.assertEquals(dict(identifier='identifier', partname='extra', data='<extra><key><sub>value</sub></key><key><sub>othervalue</sub></key><key><sub>value</sub></key><key><sub>separatedbyvalue</sub></key></extra>'), intercept.calledMethods[0].kwargs)
        # Filtering of duplicate keys is removed. (Was introduced in 3.4.4)
        # The generated XML will eventually create a LuceneDocument, the sequence of values is important
        # for phrasequeries.

    def testWorksWithRealTransactionScope(self):
        intercept = CallTrace('Intercept', ignoredAttributes=['begin', 'commit', 'rollback'])
        class MockVenturi(Observable):
            def all_unknown(self, message, *args, **kwargs):
                self.ctx.tx.locals['id'] = 'an:identifier'
                yield self.all.unknown(message, *args, **kwargs)
        class MockMultiFielder(Observable):
            def add(self, *args, **kwargs):
                self.do.addField('field.name', 'MyName')
                self.do.addField('field.name', 'AnotherName')
                self.do.addField('field.title', 'MyDocument')
                yield 'ok'
        root = be(
            (Observable(),
                (TransactionScope(transactionName="xmlDocument"),
                    (MockVenturi(),
                        (MockMultiFielder(),
                            (ResourceManager("xmlDocument"),
                                (Fields2Xml(partName="partname"),
                                    (intercept,),
                                )
                            )
                        )
                    )
                )
            )
        )
        list(compose(root.all.add('some', 'arguments')))
        self.assertEquals(['add'], [m.name for m in intercept.calledMethods])
        method = intercept.calledMethods[0]
        expectedXml = "<partname><field><name>MyName</name></field><field><name>AnotherName</name></field><field><title>MyDocument</title></field></partname>"
        self.assertEquals(((), {'identifier': 'an:identifier', 'partname': 'partname', 'data': expectedXml}), (method.args, method.kwargs))


    def testPartNameIsDefinedAtInitialization(self):
        __callstack_var_tx__ = CallTrace('TX')
        __callstack_var_tx__.locals = {'id': 'otherIdentifier'}
        intercept = CallTrace()
        fields2Xml = Fields2Xml('partName')
        fields2Xml.addObserver(intercept)
        def f():
            f = yield fields2Xml.beginTransaction()
            yield f
        f = compose(f()).next()
        f.addField('key.sub', 'value')
        list(compose(f.commit()))
        
        self.assertEquals('otherIdentifier', intercept.calledMethods[0].kwargs['identifier'])
        self.assertEquals('partName', intercept.calledMethods[0].kwargs['partname'])
        xml = bind_string(intercept.calledMethods[0].kwargs['data'])
        self.assertEquals('partName', str(xml.childNodes[0].localName))

    def testNamespace(self):
        __callstack_var_tx__ = CallTrace('TX')
        __callstack_var_tx__.locals = {'id': 'identifier'}
        intercept = CallTrace()
        fields2Xml = Fields2Xml('extra', namespace="http://meresco.org/namespace/fields/extra")
        fields2Xml.addObserver(intercept)
        def f():
            f = yield fields2Xml.beginTransaction()
            yield f
        f = compose(f()).next()
        f.addField('key.sub', 'value')
        list(compose(f.commit()))
        
        self.assertEquals(dict(identifier='identifier', partname='extra', data='<extra xmlns="http://meresco.org/namespace/fields/extra"><key><sub>value</sub></key></extra>'), intercept.calledMethods[0].kwargs)

    def testIllegalPartNameRaisesException(self):
        for partname in ['this is wrong', '%%@$%*^$^', '/slash', 'dot.dot']:
            try:
                Fields2Xml(partname)
                self.fail('Expected error for ' + partname)
            except Fields2XmlException, e:
                self.assertTrue(partname in str(e))

    def testGenerateOneKeyXml(self):
        self.assertEquals('<key>value</key>', generateXml([('key','value')]))

    def testGenerateOneKeyXml(self):
        self.assertEquals('<key>value</key>', generateXml([('key','value')]))
    
    def testGenerateOneSubKeyXml(self):
        self.assertEquals('<key><sub>value</sub></key>', generateXml([('key.sub','value')]))
   
    def testGenerateOtherParentKeyXml(self):
        self.assertEquals('<a><b>value</b></a><c><d>value2</d></c>', generateXml([('a.b','value'), ('c.d','value2')]))

    def testGenerateXml(self):
        self.assertEquals('<a><b><c><d>DDD</d></c></b></a><a><b><c><e>EEE</e></c></b></a><a><b><c>CCC</c></b></a><a><b><f>FFF</f></b></a><a><b><c><d>DDD</d></c></b></a>', generateXml([('a.b.c.d','DDD'), ('a.b.c.e','EEE'), ('a.b.c', 'CCC'),('a.b.f', 'FFF'), ('a.b.c.d', 'DDD')]))

    def testEscapeTagNamesAndValues(self):
        try:
            generateXml([('k/\\.sub','value')])
            self.fail()
        except Fields2XmlException, e:
            self.assertTrue('k/\\.sub' in str(e))


        self.assertEquals('<key>&lt;/tag&gt;</key>', generateXml([('key','</tag>')]))

    def testEscapeCorrectly(self):
        fields = [
               ( 'vuur.aap' , 'normal' ),
               ( 'vuurboom.aap' , 'normal' ),
            ]
        x = '<root>%s</root>' % generateXml(fields)
        self.assertEquals("<root><vuur><aap>normal</aap></vuur><vuurboom><aap>normal</aap></vuurboom></root>", x)



