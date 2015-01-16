## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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
from seecr.test import CallTrace

from weightless.core import compose
from meresco.core import Observable
from meresco.components import Xml2Fields

from lxml.etree import parse
from io import StringIO


def parselxml(aString):
    return parse(StringIO(aString)).getroot()


class Xml2FieldsTest(TestCase):
    def setUp(self):
        xml2fields = Xml2Fields()
        self.observer = CallTrace('Observer')
        xml2fields.addObserver(self.observer)
        self.observable = Observable()
        self.observable.addObserver(xml2fields)

    def testOneField(self):
        result = list(compose(self.observable.all.add('id0','partName', parselxml('<fields><tag>value</tag></fields>'))))
        self.assertEqual([], result)
        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertEqual(
            dict(name='addField', args=(), kwargs=dict(name='fields.tag', value='value')), 
            self.observer.calledMethods[0].asDict())

    def testDoNotIncludeNamespaces(self):
        list(compose(self.observable.all.add('id0','partName', parselxml('<fields xmlns="aap"><tag>value</tag></fields>'))))
        self.assertEqual(1, len(self.observer.calledMethods))
        self.assertEqual(
            dict(name='addField', args=(), kwargs=dict(name='fields.tag', value='value')), 
            self.observer.calledMethods[0].asDict())

    def testMultiLevel(self):
        node = parselxml("""<lom>
            <general>
                <title>The title</title>
            </general>
        </lom>""")
        list(compose(self.observable.all.add('id', 'legacy partname', node)))
        self.assertEqual(
            dict(name='addField', args=(), kwargs=dict(name='lom.general.title', value='The title')), 
            self.observer.calledMethods[0].asDict())

    def testMultipleValuesForField(self):
        node = parselxml("""<tag>
            <name>Name One</name>
            <name>Name Two</name>
        </tag>""")
        list(compose(self.observable.all.add('id', 'legacy partname', node)))
        self.assertEqual(2, len(self.observer.calledMethods))
        self.assertEqual(dict(
            name='addField', 
            args=(), 
            kwargs=dict(
                name='tag.name', 
                value='Name One')), self.observer.calledMethods[0].asDict())
        self.assertEqual(dict(
            name='addField', 
            args=(), 
            kwargs=dict(
                name='tag.name', 
                value='Name Two')), self.observer.calledMethods[1].asDict())

    def testIgnoreCommentsAndEmptyTags(self):
        node = parselxml("""<tag>
            <!-- comment line, ignore me -->
            <name>Name One</name>
            <name>Name Two</name>
            <name>
            </name>
        </tag>""")
        list(compose(self.observable.all.add('id', 'legacy partname', node)))
        self.assertEqual(2, len(self.observer.calledMethods))
        self.assertEqual(dict(
            name='addField', 
            args=(), 
            kwargs=dict(
                name='tag.name', 
                value='Name One')), self.observer.calledMethods[0].asDict())
        self.assertEqual(dict(
            name='addField', 
            args=(), 
            kwargs=dict(
                name='tag.name', 
                value='Name Two')), self.observer.calledMethods[1].asDict())

