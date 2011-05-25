# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2009-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2009-2011 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.components.autocomplete import Autocomplete

from cq2utils import CQ2TestCase, CallTrace
from weightless.core import compose

class AutocompleteTest(CQ2TestCase):
    def testHandleRequest(self):
        auto = Autocomplete(path='/some/path', maxresults=50, inputs=[('mainsearchinput', 'drilldown.dc.subject')])
        observer = CallTrace('observer')
        auto.addObserver(observer)
        observer.returnValues['prefixSearch'] = [('term0', 1),('term<1>', 3)]

        head,body = ''.join(compose(auto.handleRequest(path='/path', arguments={'prefix':['t'], 'fieldname':['field0']}))).split('\r\n'*2)

        self.assertEqualsWS("""<?xml version="1.0" encoding="utf-8"?>
<root>
    <item count="1">term0</item>
    <item count="3">term&lt;1&gt;</item>
</root>""", body)
        self.assertEquals(['prefixSearch'], [m.name for m in observer.calledMethods])
        self.assertEquals({'prefix':'t', 'fieldname':'field0', 'maxresults':50}, observer.calledMethods[0].kwargs)

    def testFieldMapping(self):
        auto = Autocomplete(path='/some/path', maxresults=50, inputs=[('mainsearchinput', 'alias')], fieldMapping={'alias': ('field1', 'field2')})
        observer = CallTrace('observer')
        auto.addObserver(observer)
        observer.returnValues['prefixSearch'] = [('term0', 1),('term<1>', 3)]

        head,body = ''.join(compose(auto.handleRequest(path='/path', arguments={'prefix':['t'], 'fieldname':['alias']}))).split('\r\n'*2)

        self.assertEquals(['prefixSearch'], [m.name for m in observer.calledMethods])
        self.assertEquals({'prefix':'t', 'fieldname':('field1', 'field2'), 'maxresults':50}, observer.calledMethods[0].kwargs)

    def testPrefixWithLabel(self):
        auto = Autocomplete(
            path='/some/path', 
            maxresults=50, 
            inputs=[('mainsearchinput', 'drilldown.dc.subject')],
            labelMapping={'author': 'some.field.with.authors'}
            )
        observer = CallTrace('observer')
        auto.addObserver(observer)
        observer.returnValues['prefixSearch'] = [('term0', 1),('term<1>', 3)]

        head,body = ''.join(compose(auto.handleRequest(
            path='/path', 
            arguments={
                'prefix': ['author=t'], 
                'fieldname': ['field0']
            }))).split('\r\n'*2)

        self.assertEqualsWS("""<?xml version="1.0" encoding="utf-8"?>
<root>
    <item count="1">author=term0</item>
    <item count="3">author=term&lt;1&gt;</item>
</root>""", body)
        self.assertEquals(['prefixSearch'], [m.name for m in observer.calledMethods])
        self.assertEquals({'prefix':'t', 'fieldname':'some.field.with.authors', 'maxresults':50}, observer.calledMethods[0].kwargs)
        
    def testPrefixWithNotExistingLabel(self):
        auto = Autocomplete(
            path='/some/path', 
            maxresults=50, 
            inputs=[('mainsearchinput', 'drilldown.dc.subject')],
            labelMapping={'author': 'some.field.with.authors'}
            )
        observer = CallTrace('observer')
        observer.returnValues['prefixSearch'] = [('term0', 1),('term<1>', 3)]
        auto.addObserver(observer)

        result = ''.join(compose(auto.handleRequest(
            path='/path', 
            arguments={'prefix': ['authorwrong=t'], 'fieldname': ['field0']})))
        header,body = result.split('\r\n'*2)
        
        self.assertEquals(['prefixSearch'], [m.name for m in observer.calledMethods])
        self.assertEquals({'prefix':'authorwrong=t', 'fieldname':'field0', 'maxresults':50}, observer.calledMethods[0].kwargs)

    def testJqueryJS(self):
        auto = Autocomplete(path='/some/path', maxresults=50, inputs=[('mainsearchinput', 'drilldown.dc.subject')])

        head,body = ''.join(compose(auto.handleRequest(path='/some/path/jquery.js', arguments={}))).split('\r\n'*2,1)

        self.assertTrue('jQuery JavaScript Library' in body, body[:300])
        try:
            self.assertTrue('Content-Type: application/x-javascript' in head, head)
        except AssertionError:
            self.assertTrue('Content-Type: application/javascript' in head, head)

    def testJqueryAutocompleteJS(self):
        auto = Autocomplete(path='/some/path', maxresults=50, inputs=[('mainsearchinput', 'drilldown.dc.subject')])

        head,body = ''.join(compose(auto.handleRequest(path='/some/path/jquery.autocomplete.js', arguments={}))).split('\r\n'*2,1)

        self.assertTrue('Extending jQuery with autocomplete' in body, body[:300])
        try:
            self.assertTrue('Content-Type: application/x-javascript' in head, head)
        except AssertionError:
            self.assertTrue('Content-Type: application/javascript' in head, head)

    def testAutocompleteJS(self):
        auto = Autocomplete(path='/some/path', maxresults=50, inputs=[('mainsearchinput', 'drilldown.dc.subject')])

        head,body = ''.join(compose(auto.handleRequest(path='/some/path/autocomplete.js', arguments={}))).split('\r\n'*2,1)

        self.assertTrue("$.get('/some/path'," in body, body[:1000])
        self.assertTrue("'fieldname': 'drilldown.dc.subject'" in body, body[:1000])
        self.assertTrue("$('#mainsearchinput').autocomplete(" in body, body[:1000])
        self.assertTrue('Content-Type: application/x-javascript' in head, head)
        self.assertTrue('Date: ' in head, head)
        self.assertTrue('Expires: ' in head, head)

    def testAutocompleteJSForMultipleInputs(self):
        auto = Autocomplete(path='/some/path',
                            maxresults=50,
                            inputs=[('mainsearchinput', 'drilldown.dc.subject'),
                                    ('anotherinput', 'anotherfield')])

        head,body = ''.join(compose(auto.handleRequest(path='/some/path/autocomplete.js', arguments={}))).split('\r\n'*2,1)

        self.assertTrue("$.get('/some/path'," in body, body[:1000])
        self.assertTrue("'fieldname': 'drilldown.dc.subject'" in body, body[:1000])
        self.assertTrue("$('#mainsearchinput').autocomplete(" in body, body[:1000])
        self.assertTrue("'fieldname': 'anotherfield'" in body, body[:1000])
        self.assertTrue("$('#anotherinput').autocomplete(" in body, body[:1000])

        self.assertTrue('Content-Type: application/x-javascript' in head, head)
        self.assertTrue('Date: ' in head, head)
        self.assertTrue('Expires: ' in head, head)
