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
# Copyright (C) 2010-2012, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012-2013, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from io import StringIO
import warnings

from seecr.test import SeecrTestCase, CallTrace
from seecr.test.io import stderr_replaced

from lxml.etree import parse
from meresco.components import lxmltostring

from meresco.components.venturi import Venturi, VenturiException
from meresco.core import TransactionScope, Observable
from meresco.core.generatorutils import asyncnoreturnvalue

from weightless.core import compose, be

def yieldNothing(**kwargs):
    return
    yield

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
                        namespaces=kwargs.get('namespaces', None)),)
                    + tuple((observer,) for observer in observers)
            )
        )
    )


class VenturiTest(SeecrTestCase):
    def testOutline(self):
        inputEvent = fromstring("""<document><part name="partone">&lt;some&gt;message&lt;/some&gt;</part><part name="parttwo"><second>message</second></part></document>""")
        interceptor = CallTrace('Interceptor', methods={'add': yieldNothing})
        v = createVenturiHelix(
                [dict(partname='partone', xpath='/document/part[@name="partone"]/text()', asData=True), dict(partname='parttwo', xpath='/document/part/second')],
                [],
                interceptor)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEqual(['begin', 'add', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEqual('identifier', interceptor.calledMethods[1].kwargs['identifier'])
        self.assertEqual('partone', interceptor.calledMethods[1].kwargs['partname'])
        self.assertEqual(b'<some>message</some>', interceptor.calledMethods[1].kwargs['data'])
        self.assertEqual('identifier', interceptor.calledMethods[2].kwargs['identifier'])
        self.assertEqual('parttwo', interceptor.calledMethods[2].kwargs['partname'])
        secondXml = interceptor.calledMethods[2].kwargs['lxmlNode']
        self.assertEqual('<second>message</second>', lxmltostring(secondXml))
        self.assertEqual('second', secondXml.getroot().tag)

    def testOnlyPassPartsSpecified(self):
        inputEvent = fromstring("""<document><part name="partone">&lt;some&gt;message&lt;/some&gt;</part><part name="parttwo"><second/></part></document>""")
        interceptor = CallTrace('Interceptor', methods={'add': yieldNothing})
        v = createVenturiHelix([{'partname': 'partone', 'xpath': '/document/part[@name="partone"]/text()'}], [], interceptor)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEqual(['begin', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEqual('<some>message</some>', lxmltostring(interceptor.calledMethods[1].kwargs['lxmlNode']))

    def testReadFromStorage(self):
        inputEvent = fromstring('<document/>')
        interceptor = CallTrace('Interceptor', ignoredAttributes=['getData', 'all_unknown', 'any_unknown', 'call_unknown'])
        interceptor.methods['add'] = yieldNothing
        storage = CallTrace('Storage', ignoredAttributes=['add', 'all_unknown'])
        storage.returnValues['getData'] = '<some>this is partone</some>'
        v = createVenturiHelix([{'partname': 'partone', 'xpath': '/document/part[@name="partone"]/text()'}], [], interceptor, storage)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEqual(['begin', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEqual('<some>this is partone</some>', lxmltostring(interceptor.calledMethods[1].kwargs['lxmlNode']))
        self.assertEqual(['begin', 'getData'], storage.calledMethodNames())
        self.assertEqual(dict(identifier='identifier', name='partone'), storage.calledMethods[1].kwargs)

    def testReadFromStorageAsString(self):
        inputEvent = fromstring('<document/>')
        interceptor = CallTrace('Interceptor', ignoredAttributes=['getData', 'all_unknown', 'call_unknown'], methods={'add': yieldNothing})
        storage = CallTrace('Storage', ignoredAttributes=['add', 'all_unknown'])
        storage.returnValues['getData'] = '<some>this is partone</some>'
        v = createVenturiHelix([dict(partname='partone', xpath='/document/part[@name="partone"]/text()', asData=True)], [], interceptor, storage)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEqual(['begin', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEqual('<some>this is partone</some>', interceptor.calledMethods[1].kwargs['data'])
        self.assertEqual(dict(identifier='identifier', name='partone'), storage.calledMethods[1].kwargs)

    def testCouldHave(self):
        inputEvent = fromstring('<document><one/></document>')
        interceptor = CallTrace('Interceptor', ignoredAttributes=['getData', 'all_unknown', 'any_unknown', 'call_unknown'], methods={'add': yieldNothing})
        v = createVenturiHelix([], [{'partname': 'one', 'xpath': '/document/one'}], interceptor)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEqual(['begin', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEqual('<one/>', lxmltostring(interceptor.calledMethods[1].kwargs['lxmlNode']))

    def testCouldHaveAsString(self):
        inputEvent = fromstring('<document><one>some text</one></document>')
        interceptor = CallTrace('Interceptor', ignoredAttributes=['getData', 'unknown'], methods={'add': yieldNothing})
        v = createVenturiHelix([], [dict(partname='one', xpath='/document/one', asData=True)], interceptor)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEqual(['begin', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEqual(b'<one>some text</one>', interceptor.calledMethods[1].kwargs['data'])

    def testCouldHaveInStorage(self):
        inputEvent = fromstring('<document><other/></document>')
        interceptor = CallTrace('Interceptor', ignoredAttributes=['getData', 'all_unknown', 'any_unknown', 'call_unknown'], methods={'add': yieldNothing})
        storage = CallTrace('Storage', ignoredAttributes=['add', 'all_unknown'])
        storage.returnValues['getData'] = '<one/>'
        v = createVenturiHelix([], [{'partname': 'one', 'xpath': '/document/one'}], interceptor, storage)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEqual(['begin', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEqual('<one/>', lxmltostring(interceptor.calledMethods[1].kwargs['lxmlNode']))
        self.assertEqual(dict(identifier='identifier', name='one'), storage.calledMethods[1].kwargs)

    def testCouldHaveButDoesnot(self):
        inputEvent = fromstring('<document><other/></document>')
        interceptor = CallTrace('Interceptor', ignoredAttributes=['getData', 'all_unknown', 'any_unknown', 'call_unknown'], methods={'add': yieldNothing})
        storage = CallTrace('Storage', ignoredAttributes=['add', 'all_unknown'])
        storage.exceptions['getData'] = KeyError('Part not available')
        v = createVenturiHelix([{'partname': 'other', 'xpath': '/document/other'}], [{'partname': 'one', 'xpath': '/document/one'}], interceptor, storage)
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEqual(['begin', 'add'], [m.name for m in interceptor.calledMethods])
        self.assertEqual('identifier', interceptor.calledMethods[1].kwargs['identifier'])
        self.assertEqual('other', interceptor.calledMethods[1].kwargs['partname'])

    def testXpathReturnsMultipleResults(self):
        inputEvent = fromstring('<document><one/><two/></document>')
        v = createVenturiHelix([{'partname': 'one', 'xpath': '/document/*'}], [])
        try:
            result = compose(v.all.add('identifier', 'document', inputEvent))
            list(result)
            self.fail('no good no')
        except Exception as e:
            self.assertEqual("XPath '/document/*' should return atmost one result.", str(e))
        finally:
            result.close()

    def testNamespace(self):
        inputEvent = fromstring('<document xmlns="ns1" xmlns:ns2="ns2"><ns2:one/><two/></document>')
        interceptor = CallTrace('Interceptor', methods={'add': yieldNothing})
        v = createVenturiHelix([{'partname': 'one', 'xpath': '/prefixone:document/prefixtwo:one'}, {'partname': 'two', 'xpath': '/prefixone:document/prefixone:two'}], [], interceptor, namespaces={'prefixone':'ns1', 'prefixtwo':'ns2'})
        list(compose(v.all.add('identifier', 'document', inputEvent)))
        self.assertEqual(['begin', 'add', 'add'], [m.name for m in interceptor.calledMethods])

    def testTransactionScopeFilledWithIdentifier(self):
        ids = []
        class TempComponent(Observable):
            @asyncnoreturnvalue
            def add(this, identifier, partname, lxmlNode):
                ids.append(this.ctx.tx.locals['id'])
        v = createVenturiHelix([{'partname': 'PARTNAME', 'xpath': '/document'}],[], TempComponent())
        list(compose(v.all.add(identifier='ID', partname='PARTNAME', lxmlNode=fromstring('<document><other/></document>'))))
        self.assertEqual(1, len(ids))

    def testDeleteAlsoSetsIdOnTransaction(self):
        __callstack_var_tx__ = CallTrace('Transaction')
        __callstack_var_tx__.locals={}
        v = Venturi(should=[{'partname': 'PARTNAME', 'xpath': '/document'}],could=[])
        list(compose(v.delete(identifier='identifier')))
        self.assertEqual('identifier', __callstack_var_tx__.locals['id'])

    def testPartInShouldDoesNotExist(self):
        inputEvent = fromstring('<document/>')
        interceptor = CallTrace('Interceptor', ignoredAttributes=['begin', 'getData', 'all_unknown', 'any_unknown', 'call_unknown'])
        storage = CallTrace('Storage', ignoredAttributes=['begin', 'add'])
        storage.exceptions['getData'] = KeyError('no')
        v = createVenturiHelix([{'partname': 'partone', 'xpath': '/document/part[@name="partone"]/text()'}], [], interceptor, storage)
        try:
            list(compose(v.all.add('identifier', 'document', inputEvent)))
            self.fail('Expected exception')
        except VenturiException:
            pass
        self.assertEqual([], [m.name for m in interceptor.calledMethods])
        self.assertEqual(['getData'], [m.name for m in storage.calledMethods])

    def testDeleteIsAsynchronous(self):
        __callstack_var_tx__ = CallTrace('Transaction')
        __callstack_var_tx__.locals={}
        observer = CallTrace('observer')
        callable = lambda: None
        observer.returnValues['delete'] = (f for f in [callable])
        v = Venturi()
        v.addObserver(observer)

        result = list(compose(v.delete(identifier='identifier')))

        self.assertEqual([callable], result)
        self.assertEqual(['delete'], [m.name for m in observer.calledMethods])

    def testNoLxmlTailOnPart(self):
        inputEvent = fromstring("""<document><part name="partone">&lt;some&gt;message&lt;/some&gt;\n\n\n\n</part><part name="parttwo"><second>message</second>\n\n\n\n</part></document>""")
        interceptor = CallTrace('Interceptor', methods={'add': yieldNothing})
        v = createVenturiHelix([{'partname': 'partone', 'xpath': '/document/part[@name="partone"]/text()'}, {'partname': 'parttwo', 'xpath': '/document/part/second'}], [], interceptor)
        list(compose(v.all.add('identifier', 'document', inputEvent)))

        self.assertEqual('<some>message</some>', lxmltostring(interceptor.calledMethods[1].kwargs['lxmlNode']))
        secondXml = interceptor.calledMethods[2].kwargs['lxmlNode']
        self.assertEqual('<second>message</second>', lxmltostring(secondXml))

    def testPartsWithUnicodeChars(self):
        inputEvent = fromstring("""<document><part name="partone">&lt;some&gt;t€xt&lt;/some&gt;\n\n\n\n</part><part name="parttwo"><second>t€xt</second>\n\n\n\n</part></document>""")
        interceptor = CallTrace('Interceptor', methods={'add': yieldNothing})
        v = createVenturiHelix([{'partname': 'partone', 'xpath': '/document/part[@name="partone"]/text()'}, {'partname': 'parttwo', 'xpath': '/document/part/second'}], [], interceptor)
        list(compose(v.all.add('identifier', 'document', inputEvent)))

        firstXml = interceptor.calledMethods[1].kwargs['lxmlNode']
        self.assertEqual('<some>t€xt</some>', lxmltostring(firstXml))
        self.assertEqual('t€xt', firstXml.getroot().text)
        secondXml = interceptor.calledMethods[2].kwargs['lxmlNode']
        self.assertEqual('<second>t€xt</second>', lxmltostring(secondXml))
        self.assertEqual('t€xt', secondXml.getroot().text)

    def testEmptyIdInAddNotAllowed(self):
        __callstack_var_tx__ = CallTrace('Transaction')
        __callstack_var_tx__.locals={}
        inputEvent = fromstring("""<document><part name="partone">&lt;some&gt;t€xt&lt;/some&gt;\n\n\n\n</part><part name="parttwo"><second>t€xt</second>\n\n\n\n</part></document>""")
        v = Venturi()
        try:
            list(compose(v.add('', 'document', inputEvent)))
            self.fail("Should raise an exception")
        except ValueError as e:
            self.assertEqual("Empty identifier not allowed.", str(e))

        try:
            list(compose(v.add(None, 'document', inputEvent)))
            self.fail("Should raise an exception")
        except ValueError as e:
            self.assertEqual("Empty identifier not allowed.", str(e))

    def testEmptyIdInDeleteNotAllowed(self):
        __callstack_var_tx__ = CallTrace('Transaction')
        __callstack_var_tx__.locals={}
        v = Venturi()
        try:
            list(compose(v.delete('')))
            self.fail("Should raise an exception")
        except ValueError as e:
            self.assertEqual("Empty identifier not allowed.", str(e))

        try:
            list(compose(v.delete(None)))
            self.fail("Should raise an exception")
        except ValueError as e:
            self.assertEqual("Empty identifier not allowed.", str(e))

    def testDeprecatedPartsSpecification(self):
        with warnings.catch_warnings():
            warnings.simplefilter("default")
            with stderr_replaced() as s:
                venturi = Venturi(should=[('partname', '/x/path')])
                self.assertTrue("Please use {'partname'" in s.getvalue())

