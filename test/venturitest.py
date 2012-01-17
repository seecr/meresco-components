# -*- coding=utf-8 -*-
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
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

from StringIO import StringIO

from seecr.test import SeecrTestCase, CallTrace
from lxml.etree import parse, tostring

from meresco.components.venturi import Venturi, VenturiException
from meresco.core import TransactionScope, Observable

from weightless.core import compose, be


def fromstring(aString):
    xmlParsed = parse(StringIO(aString))
    return xmlParsed

def createVenturiHelix(should, could, *observers, **kwargs):
    return be(
        (Observable(),
            (TransactionScope('document'),
                (Venturi(
                        should=should,
                        could=could,
                        namespaceMap=kwargs.get('namespaceMap', {})),)
                    +tuple((observer,) for observer in observers)
            )
        )
    )

class VenturiTest(SeecrTestCase):
    def testOutline(self):
        inputEvent = fromstring("""<document><part name="partone">&lt;some&gt;message&lt;/some&gt;</part><part name="parttwo"><second>message</second></part></document>""")
        interceptor = CallTrace('Interceptor')
        v = createVenturiHelix([('partone', '/document/part[@name="partone"]/text()'), ('parttwo', '/document/part/second')], [], interceptor)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEquals(['begin', 'add', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEquals('identifier', interceptor.calledMethods[1].kwargs['identifier'])
        self.assertEquals('partone', interceptor.calledMethods[1].kwargs['partname'])
        self.assertEquals('<some>message</some>', tostring(interceptor.calledMethods[1].kwargs['lxmlNode']))
        self.assertEquals('identifier', interceptor.calledMethods[2].kwargs['identifier'])
        self.assertEquals('parttwo', interceptor.calledMethods[2].kwargs['partname'])
        secondXml = interceptor.calledMethods[2].kwargs['lxmlNode']
        self.assertEquals('<second>message</second>', tostring(secondXml))
        self.assertEquals('second', secondXml.getroot().tag)


    def testOnlyPassPartsSpecified(self):
        inputEvent = fromstring("""<document><part name="partone">&lt;some&gt;message&lt;/some&gt;</part><part name="parttwo"><second/></part></document>""")
        interceptor = CallTrace('Interceptor')
        v = createVenturiHelix([('partone', '/document/part[@name="partone"]/text()')], [], interceptor)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEquals(['begin', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEquals('<some>message</some>', tostring(interceptor.calledMethods[1].kwargs['lxmlNode']))

    def testReadFromStorage(self):
        inputEvent = fromstring('<document/>')
        interceptor = CallTrace('Interceptor', ignoredAttributes=['isAvailable', 'getStream', 'all_unknown', 'any_unknown', 'call_unknown'])
        storage = CallTrace('Storage', ignoredAttributes=['add'])
        storage.returnValues['isAvailable'] = (True, True)
        storage.returnValues['getStream'] = StringIO('<some>this is partone</some>')
        v = createVenturiHelix([('partone', '/document/part[@name="partone"]/text()')], [], interceptor, storage)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEquals(['begin', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEquals('<some>this is partone</some>', tostring(interceptor.calledMethods[1].kwargs['lxmlNode']))
        self.assertEquals(('identifier', 'partone'), storage.calledMethods[1].args)

    def testCouldHave(self):
        inputEvent = fromstring('<document><one/></document>')
        interceptor = CallTrace('Interceptor', ignoredAttributes=['getStream', 'all_unknown', 'any_unknown', 'call_unknown'])
        v = createVenturiHelix([], [('one', '/document/one')], interceptor)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEquals(['begin', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEquals('<one/>', tostring(interceptor.calledMethods[1].kwargs['lxmlNode']))

    def testCouldHaveInStorage(self):
        inputEvent = fromstring('<document><other/></document>')
        interceptor = CallTrace('Interceptor', ignoredAttributes=['isAvailable', 'getStream', 'all_unknown', 'any_unknown', 'call_unknown'])
        storage = CallTrace('Storage', ignoredAttributes=['add'])
        storage.returnValues['isAvailable'] = (True, True)
        storage.returnValues['getStream'] = StringIO('<one/>')
        v = createVenturiHelix([], [('one', '/document/one')], interceptor, storage)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEquals(['begin', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEquals('<one/>', tostring(interceptor.calledMethods[1].kwargs['lxmlNode']))
        self.assertEquals(('identifier', 'one'), storage.calledMethods[1].args)

    def testCouldHaveButDoesnot(self):
        inputEvent = fromstring('<document><other/></document>')
        interceptor = CallTrace('Interceptor', ignoredAttributes=['isAvailable', 'getStream', 'all_unknown', 'any_unknown', 'call_unknown'])
        storage = CallTrace('Storage', ignoredAttributes=['add'])
        storage.exceptions['getStream'] = KeyError('Part not available')
        v = createVenturiHelix([('other', '/document/other')], [('one', '/document/one')], interceptor, storage)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEquals(['begin', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEquals('identifier', interceptor.calledMethods[1].kwargs['identifier'])
        self.assertEquals('other', interceptor.calledMethods[1].kwargs['partname'])

    def testXpathReturnsMultipleResults(self):
        inputEvent = fromstring('<document><one/><two/></document>')
        v = createVenturiHelix([('one', '/document/*')], [])
        try:
            result = compose(v.all.add('identifier', 'document', inputEvent))
            list(result)
            self.fail('no good no')
        except Exception, e:
            self.assertEquals("XPath '/document/*' should return atmost one result.", str(e))
        finally:
            result.close()

    def testNamespace(self):
        inputEvent = fromstring('<document xmlns="ns1" xmlns:ns2="ns2"><ns2:one/><two/></document>')
        interceptor = CallTrace('Interceptor')
        v = createVenturiHelix([('one', '/prefixone:document/prefixtwo:one'), ('two','/prefixone:document/prefixone:two')], [], interceptor, namespaceMap={'prefixone':'ns1', 'prefixtwo':'ns2'})
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEquals(['begin', 'add', 'add'], [m.name for m in interceptor.calledMethods])

    def testTransactionScopeFilledWithIdentifier(self):
        ids = []
        class TempComponent(Observable):
            def add(this, identifier, partname, lxmlNode):
                ids.append(this.ctx.tx.locals['id'])
        v = createVenturiHelix([('PARTNAME', '/document')],[], TempComponent())
        list(compose(v.all.add(identifier='ID', partname='PARTNAME', lxmlNode=fromstring('<document><other/></document>'))))
        self.assertEquals(1, len(ids))

    def testDeleteAlsoSetsIdOnTransaction(self):
        __callstack_var_tx__ = CallTrace('Transaction')
        __callstack_var_tx__.locals={}
        v = Venturi(should=[('PARTNAME', '/document')],could=[])
        list(compose(v.delete(identifier='identifier')))
        self.assertEquals('identifier', __callstack_var_tx__.locals['id'])

    def testPartInShouldDoesNotExist(self):
        inputEvent = fromstring('<document/>')
        interceptor = CallTrace('Interceptor', ignoredAttributes=['begin', 'isAvailable', 'getStream', 'all_unknown', 'any_unknown', 'call_unknown'])
        storage = CallTrace('Storage', ignoredAttributes=['begin', 'add'])
        storage.returnValues['isAvailable'] = (False, False)
        v = createVenturiHelix([('partone', '/document/part[@name="partone"]/text()')], [], interceptor, storage)
        try:
            list(compose(v.all.add('identifier', 'document', inputEvent)))
            self.fail('Expected exception')
        except VenturiException:
            pass
        self.assertEquals([], [m.name for m in interceptor.calledMethods])
        self.assertEquals(['isAvailable'], [m.name for m in storage.calledMethods])

    def testDeleteIsAsynchronous(self):
        __callstack_var_tx__ = CallTrace('Transaction')
        __callstack_var_tx__.locals={}
        observer = CallTrace('observer')
        callable = lambda: None
        observer.returnValues['delete'] = (f for f in [callable])
        v = Venturi()
        v.addObserver(observer)

        result = list(compose(v.delete(identifier='identifier')))

        self.assertEquals([callable], result)
        self.assertEquals(['delete'], [m.name for m in observer.calledMethods])

    def testNoLxmlTailOnPart(self):
        inputEvent = fromstring("""<document><part name="partone">&lt;some&gt;message&lt;/some&gt;\n\n\n\n</part><part name="parttwo"><second>message</second>\n\n\n\n</part></document>""")
        interceptor = CallTrace('Interceptor')
        v = createVenturiHelix([('partone', '/document/part[@name="partone"]/text()'), ('parttwo', '/document/part/second')], [], interceptor)
        list(compose(v.all.add('identifier', 'document', inputEvent)))

        self.assertEquals('<some>message</some>', tostring(interceptor.calledMethods[1].kwargs['lxmlNode']))
        secondXml = interceptor.calledMethods[2].kwargs['lxmlNode']
        self.assertEquals('<second>message</second>', tostring(secondXml))

    def testPartsWithUnicodeChars(self):
        inputEvent = fromstring("""<document><part name="partone">&lt;some&gt;t€xt&lt;/some&gt;\n\n\n\n</part><part name="parttwo"><second>t€xt</second>\n\n\n\n</part></document>""")
        interceptor = CallTrace('Interceptor')
        v = createVenturiHelix([('partone', '/document/part[@name="partone"]/text()'), ('parttwo', '/document/part/second')], [], interceptor)
        list(compose(v.all.add('identifier', 'document', inputEvent)))

        firstXml = interceptor.calledMethods[1].kwargs['lxmlNode']
        self.assertEquals('<some>t&#8364;xt</some>', tostring(firstXml))
        self.assertEquals('t€xt', firstXml.getroot().text)
        secondXml = interceptor.calledMethods[2].kwargs['lxmlNode']
        self.assertEquals('<second>t&#8364;xt</second>', tostring(secondXml))
        self.assertEquals('t€xt', secondXml.getroot().text)

