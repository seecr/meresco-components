## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
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

from weightless.core import be, compose
from meresco.core import Observable
from meresco.components import RenameField, TransformFieldValue, FilterField, AddField, Xml2Fields, FilterFieldValue
from lxml.etree import parse
from io import StringIO

class FieldletsTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.observert = CallTrace('Observer')

    def testRenameField(self):
        dna = be(
            (Observable(),
                (RenameField(lambda name: name + '.fieldname'),
                    (self.observert, )
                )
            )
        )

        dna.do.addField(name='fieldname', value="x")
        self.assertEqual(1, len(self.observert.calledMethods))
        self.assertEqual({
            'name': 'addField',
            'args': (),
            'kwargs': {
                'name': 'fieldname.fieldname',
                'value': 'x'}
            }, self.observert.calledMethods[0].asDict())

    def testTransformFieldValueWithTransform(self):
        dna = be(
            (Observable(),
                (TransformFieldValue(lambda value: 'transform ' + value),
                    (self.observert, )
                )
            )
        )

        dna.do.addField(name='f', value="x")
        self.assertEqual(1, len(self.observert.calledMethods))
        self.assertEqual({
            'name': 'addField',
            'args': (),
            'kwargs': {
                'name': 'f',
                'value': 'transform x'}
            }, self.observert.calledMethods[0].asDict())

    def testAddField(self):
        dna = be(
            (Observable(),
                (AddField(name='name', value='value'),
                    (self.observert, )
                )
            )
        )

        list(compose(dna.all.add(identifier='id', partname='part', lxmlNode='data')))
        self.assertEqual(1, len(self.observert.calledMethods))
        self.assertEqual({
            'name': 'addField', 
            'args': (), 
            'kwargs': {'name': 'name', 'value': 'value'}}, self.observert.calledMethods[0].asDict())

    def testDoNotTransformFieldValueForTransformWithNoneResult(self):
        dna = be(
            (Observable(),
                (TransformFieldValue(lambda value: None),
                    (self.observert, )
                )
            )
        )

        dna.do.addField(name='f', value="x")
        self.assertEqual(0, len(self.observert.calledMethods))

    def testIntegration(self):
        dna = be(
            (Observable(),
                (AddField(name='addfield.name', value='addfield.value'),
                    (self.observert,)
                ),
                (Xml2Fields(),
                    (self.observert,),
                    (FilterField(lambda name:name in ['base.name1']),
                        (RenameField(lambda name:'drilldown.'+name),
                            (self.observert,)
                        )
                    ),
                    (FilterField(lambda name:name in ['base.name2']),
                        (TransformFieldValue(lambda value: value.upper()),
                            (RenameField(lambda name:'normalize.'+name),
                                (self.observert,)
                            )
                        ),
                        (TransformFieldValue(lambda value: None),
                            (RenameField(lambda name:'normalize2.'+name),
                                (self.observert,)
                            )
                        ),
                        (TransformFieldValue(lambda value: value),
                            (RenameField(lambda name:'normalize3.'+name),
                                (self.observert,)
                            )
                        )
                    ),
                    (RenameField(lambda name:'valuefilter.'+name),
                        (FilterFieldValue(lambda value: 'value2' in value),
                            (self.observert,)
                        )
                    )
                )
            )
        )
        inputXml = """<base>
    <name1>value1</name1>
    <name2>value2</name2>
    <name3>value3</name3>
</base>"""
        
        result = list(compose(dna.all.add(identifier='id', partname='part', lxmlNode=parse(StringIO(inputXml)))))
        self.assertEqual([], result)

        self.assertEqual([
            {'name': 'addField', 'args': (), 'kwargs': {'name': 'addfield.name', 'value': 'addfield.value'}},
            {'name': 'addField', 'args': (), 'kwargs': {'name': 'base.name1', 'value': 'value1'}},
            {'name': 'addField', 'args': (), 'kwargs': {'name': 'drilldown.base.name1', 'value': 'value1'}},
            {'name': 'addField', 'args': (), 'kwargs': {'name': 'base.name2', 'value': 'value2'}},
            {'name': 'addField', 'args': (), 'kwargs': {'name': 'normalize.base.name2', 'value': 'VALUE2'}},
            {'name': 'addField', 'args': (), 'kwargs': {'name': 'normalize3.base.name2', 'value': 'value2'}},
            {'name': 'addField', 'args': (), 'kwargs': {'name': 'valuefilter.base.name2', 'value': 'value2'}},
            {'name': 'addField', 'args': (), 'kwargs': {'name': 'base.name3', 'value': 'value3'}},
            ], [m.asDict() for m in self.observert.calledMethods])

