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

from seecr.test import SeecrTestCase, CallTrace
from meresco.xml import XMLRewrite

from StringIO import StringIO
from lxml.etree import parse, tostring, XMLParser
from difflib import unified_diff

from re import match
from os import remove

from meresco.components import Crosswalk
from meresco.components.crosswalk import rewriteRules
from meresco.components.xml_generic import Validate, __file__ as xml_genericpath
from weightless.core import compose
from os.path import join, dirname, abspath

def readRecord(name):
    return open('data/' + name)

class CrosswalkTest(SeecrTestCase):

    def setUp(self):
        SeecrTestCase.setUp(self)
        self.crosswalk = Crosswalk()
        self.validate = Validate(join(abspath(dirname(xml_genericpath)), 'schemas-lom', 'lomCc.xsd'))
        self.crosswalk.addObserver(self.validate)
        self.observer = CallTrace()
        self.validate.addObserver(self.observer)

    def testOne(self):
        list(compose(self.crosswalk.all_unknown('crosswalk', 'id', 'metadata', theXmlRecord=parse(readRecord('imsmd_v1p2-1.xml')))))
        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertEquals(2, len(self.observer.calledMethods[0].args))
        arguments = self.observer.calledMethods[0].args
        self.assertEquals("id", arguments[0])
        self.assertEquals("metadata", arguments[1])

    def testValidate(self):
        list(compose(self.validate.all_unknown('methodname', 'id', 'metadata', parse(readRecord('lom-cc-nbc.xml')))))
        try:
            list(compose(self.validate.all_unknown('methodname', 'id', 'metadata', parse(readRecord('imsmd_v1p2-1.xml')))))
            self.fail('must raise exception')
        except Exception, e:
            self.assertTrue("ERROR:SCHEMASV:SCHEMAV_CVC_ELT_1: Element '{http://dpc.uba.uva.nl/schema/lom/triplel}lom': No matching global declaration available for the validation root." in str(e), str(e))

    def testTripleLExample(self):
        try:
            list(compose(self.crosswalk.all_unknown('methodname', 'id', 'metadata', theXmlRecord=parse(readRecord('triple-lrecord.xml')))))
        except Exception, e:
            message = readRecord('triple-lrecord.xml').read()
            for n, line in enumerate(message.split('\n')):
                print n+1, line
            raise

    def testNormalize(self):
        list(compose(self.crosswalk.all_unknown('add', None, 'metadata', theXmlRecord=parse(readRecord('triple-lrecord.xml')))))
        self.assertEquals(1, len(self.observer.calledMethods))
        self.assertFalse('2006-11-28 19:00' in tostring(self.observer.calledMethods[0].kwargs['theXmlRecord']))

    def testReplacePrefix(self):
        rules = [('classification/taxonPath/taxon/entry', 'imsmd:classification/imsmd:taxonpath/imsmd:taxon/imsmd:entry', ('imsmd:langstring/@xml:lang', 'imsmd:langstring'), '<string language="%s">%s</string>',
        [('\s*\d+\s*(\w+)', '%s', (str,))])]
        newRules = rewriteRules('imsmd', '', rules)
        self.assertEquals(rules[0][-1], newRules[0][-1])

    def testAddCustomNormalizeMethods(self):
        open(join(self.tempdir, 'my.rules'), 'w').write("""
inputNamespace = defaultNameSpace = 'CrosswalkTest'
vocabDict = {}
rootTagName = 'new'
sourceNsMap = {
    'src': inputNamespace
}

newNsMap = {
    'dst': inputNamespace
}
rules = [
('dst:two', 'src:one', ('src:sub1', 'src:sub2'), '%s', myNormalizeMethod)
]
""")
        c = Crosswalk(rulesDir=self.tempdir, extraGlobals={'myNormalizeMethod': lambda x,y:(x+' '+y,)})
        node = parse(StringIO("""<old xmlns="CrosswalkTest"><one><sub1>first</sub1><sub2>second</sub2></one></old>"""))
        newNode = c.convert(node)
        self.assertEquals(['first second'], newNode.xpath("/dst:new/dst:two/text()", namespaces={'dst':'CrosswalkTest'}))

    def testXPathNodeTest(self):
        x = """
        <x>
            <y>
                <p>
                    <q>selector</q>
                </p>
                <z>aap</z>
            </y>
            <y>
                <p>
                    <q>not-selector</q>
                </p>
                <z>mies</z>
            </y>
        </x>
        """
        tree = parse(StringIO(x))
        result = tree.xpath('y')
        self.assertEquals(2, len(result))
        result = tree.xpath('y[p/q="selector"]')
        self.assertEquals(1, len(result))
        self.assertEquals('y', result[0].tag)
