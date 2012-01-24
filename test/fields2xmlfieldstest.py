# -*- coding: utf-8 -*-
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

from seecr.test import SeecrTestCase, CallTrace
from meresco.components.fields2xmlfields import Fields2XmlFields, generateXml
from meresco.core import Observable, TransactionScope
from weightless.core import compose, be

NAMESPACE="http://example.org/namespace"

def add(identifier, partname, data):
    return
    yield

class Fields2XmlFieldsTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)

        ctx = CallTrace('CTX')
        tx = CallTrace('TX', returnValues={'getId': 1234})
        tx.locals = {'id': 'identifier'}
        tx.name = "tsName"
        self.fxf = Fields2XmlFields("tsName", "fields-partname", namespace=NAMESPACE)
        self.fxf.ctx = ctx 
        self.fxf.ctx.tx = tx
        self.observer = CallTrace(methods={'add': add})
        self.fxf.addObserver(self.observer)

    def testAddField(self):
        self.fxf.begin(name='tsName')
        self.fxf.addField("key.sub", "value")
        list(compose(self.fxf.commit(id=1234)))
        self.assertEquals(["add"], [m.name for m in self.observer.calledMethods])
        kwargs = self.observer.calledMethods[0].kwargs
        self.assertEquals("identifier", kwargs['identifier'])
        self.assertEquals("fields-partname", kwargs['partname'])
        self.assertEqualsWS("""<fields xmlns="%s">
                <field name="key.sub">value</field>
            </fields>""" % NAMESPACE, kwargs['data'])

    def testAddFieldWithXmlInKeyAndValue(self):
        self.fxf.begin(name='tsName')
        self.fxf.addField("""<name>"&'""", """<value>"&'""")
        list(compose(self.fxf.commit(id=1234)))
        self.assertEquals(["add"], [m.name for m in self.observer.calledMethods])
        kwargs = self.observer.calledMethods[0].kwargs
        self.assertEqualsWS("""<fields xmlns="%s">
                <field name="&lt;name&gt;&quot;&amp;'">&lt;value&gt;&quot;&amp;'</field>
            </fields>""" % NAMESPACE, kwargs['data'])

    def testNoCommitWhenAddFieldNotCalled(self):
        self.fxf.begin(name='tsName')
        list(compose(self.fxf.commit(id=1234)))
        self.assertEquals([], self.observer.calledMethods)

    def testWorksWithRealTransactionScope(self):
        intercept = CallTrace('Intercept', ignoredAttributes=['begin', 'commit', 'rollback'], methods={'add': add})
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
        mockMultiFielder = MockMultiFielder()
        root = be(
            (Observable(),
                (TransactionScope(transactionName='xmlDocument'),
                    (MockVenturi(),
                        (mockMultiFielder,
                            (Fields2XmlFields(transactionName='xmlDocument', partname='partname'),
                                (intercept,),
                            )
                        )
                    )
                )
            )
        )

        list(compose(root.all.add('some', 'arguments')))
        self.assertEquals(['add'], [m.name for m in intercept.calledMethods])
        method = intercept.calledMethods[0]
        expectedXml = '<fields><field name="field.name">MyName</field><field name="field.name">AnotherName</field><field name="field.title">MyDocument</field></fields>'
        self.assertEquals(((), {'identifier': 'an:identifier', 'partname': 'partname', 'data': expectedXml}), (method.args, method.kwargs))

    def testSameAddFieldGeneratedTwoTimes(self):
        self.fxf.begin(name='tsName')
        self.fxf.addField("key.sub", "value")
        self.fxf.addField("key.sub", "othervalue")
        self.fxf.addField("key.sub", "value")
        self.fxf.addField("key.sub", "separatedbyvalue")
        list(compose(self.fxf.commit(id=1234)))

        self.assertEquals(['add'], [m.name for m in self.observer.calledMethods])
        self.assertEqualsWS("""<fields xmlns="%s">
               <field name="key.sub">value</field>
               <field name="key.sub">othervalue</field>
               <field name="key.sub">value</field>
               <field name="key.sub">separatedbyvalue</field>
            </fields>""" % NAMESPACE, self.observer.calledMethods[0].kwargs['data'])

    def testEmptyNamespace(self):
        ctx = CallTrace('CTX')
        tx = CallTrace('TX', returnValues={'getId': 1234})
        tx.locals = {'id': 'identifier'}
        tx.name = "tsName"
        fxf = Fields2XmlFields("tsName", "fields-partname")
        fxf.ctx = ctx 
        fxf.ctx.tx = tx
        observer = CallTrace(methods={'add': add})
        fxf.addObserver(observer)
        
        fxf.begin(name='tsName')
        fxf.addField("key.sub", "value")
        list(compose(fxf.commit(id=1234)))

        self.assertEquals(['add'], [m.name for m in observer.calledMethods])
        self.assertEqualsWS("""<fields>
                <field name="key.sub">value</field>
            </fields>""", observer.calledMethods[0].kwargs['data']) 

    def testGenerateOneKeyXml(self):
        self.assertEquals('<field name="key">value</field>', generateXml([('key','value')]))

    def testGenerateOneSubKeyXml(self):
        self.assertEquals('<field name="key.sub">value</field>', generateXml([('key.sub','value')]))
   
    def testGenerateOtherParentKeyXml(self):
        self.assertEquals('<field name="a.b">value</field><field name="c.d">value2</field>', generateXml([('a.b','value'), ('c.d','value2')]))

    def testGenerateXml(self):
        self.assertEquals('<field name="a.b.c.d">DDD</field><field name="a.b.c.e">EEE</field><field name="a.b.c">CCC</field><field name="a.b.f">FFF</field><field name="a.b.c.d">DDD</field>', generateXml([('a.b.c.d','DDD'), ('a.b.c.e','EEE'), ('a.b.c', 'CCC'),('a.b.f', 'FFF'), ('a.b.c.d', 'DDD')]))

    def testEscapeTagNamesAndValues(self):
        self.assertEquals("""<field name="k/\\.sub">value</field>""", generateXml([('k/\\.sub','value')]))
        self.assertEquals('<field name="key">&lt;/tag&gt;</field>', generateXml([('key','</tag>')]))

    def testEscapeCorrectly(self):
        fields = [
               ( 'vuur.aap' , 'normal' ),
               ( 'vuurboom.aap' , 'normal' ),
            ]
        x = '<root>%s</root>' % generateXml(fields)
        self.assertEquals("""<root><field name="vuur.aap">normal</field><field name="vuurboom.aap">normal</field></root>""", x)

