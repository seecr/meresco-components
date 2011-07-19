# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
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

from cq2utils import CQ2TestCase, CallTrace
from meresco.components.fields2xmlfields import Fields2XmlFields, generateXml

NAMESPACE="http://example.org/namespace"

class Fields2XmlFieldsTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)

        ctx = CallTrace('CTX')
        tx = CallTrace('TX')
        tx.locals = {'id': 'identifier'}
        tx.name = "tsName"
        self.fxf = Fields2XmlFields("tsName", "fields-partname", namespace=NAMESPACE)
        self.fxf.ctx = ctx 
        self.fxf.ctx.tx = tx
        self.observer = CallTrace()
        self.fxf.addObserver(self.observer)

    def testAddField(self):
        self.fxf.begin()
        self.fxf.addField("key.sub", "value")
        self.fxf.commit()
        self.assertEquals(["add"], [m.name for m in self.observer.calledMethods])
        kwargs = self.observer.calledMethods[0].kwargs
        self.assertEquals("identifier", kwargs['identifier'])
        self.assertEquals("fields-partname", kwargs['partname'])
        self.assertEqualsWS("""<fields xmlns="%s">
                <field name="key.sub">value</field>
            </fields>""" % NAMESPACE, kwargs['data'])

    def testAddFieldWithXmlInKeyAndValue(self):
        self.fxf.begin()
        self.fxf.addField("""<name>"&'""", """<value>"&'""")
        self.fxf.commit()
        self.assertEquals(["add"], [m.name for m in self.observer.calledMethods])
        kwargs = self.observer.calledMethods[0].kwargs
        self.assertEqualsWS("""<fields xmlns="%s">
                <field name="&lt;name&gt;&quot;&amp;'">&lt;value&gt;&quot;&amp;'</field>
            </fields>""" % NAMESPACE, kwargs['data'])

    def testNoCommitWhenAddFieldNotCalled(self):
        self.fxf.begin()
        self.fxf.commit()
        self.assertEquals([], self.observer.calledMethods)

    def testSameAddFieldGeneratedTwoTimes(self):
        self.fxf.begin()
        self.fxf.addField("key.sub", "value")
        self.fxf.addField("key.sub", "othervalue")
        self.fxf.addField("key.sub", "value")
        self.fxf.addField("key.sub", "separatedbyvalue")
        self.fxf.commit()

        self.assertEquals(['add'], [m.name for m in self.observer.calledMethods])
        self.assertEqualsWS("""<fields xmlns="%s">
               <field name="key.sub">value</field>
               <field name="key.sub">othervalue</field>
               <field name="key.sub">value</field>
               <field name="key.sub">separatedbyvalue</field>
            </fields>""" % NAMESPACE, self.observer.calledMethods[0].kwargs['data'])

    def testEmptyNamespace(self):
        ctx = CallTrace('CTX')
        tx = CallTrace('TX')
        tx.locals = {'id': 'identifier'}
        tx.name = "tsName"
        fxf = Fields2XmlFields("tsName", "fields-partname")
        fxf.ctx = ctx 
        fxf.ctx.tx = tx
        observer = CallTrace()
        fxf.addObserver(observer)
        
        fxf.begin()
        fxf.addField("key.sub", "value")
        fxf.commit()

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

