# -*- coding: utf-8 -*-

from merescocomponents.autocomplete import Autocomplete

from cq2utils import CQ2TestCase, CallTrace
from weightless import compose

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
        self.assertTrue('Content-Type: application/x-javascript' in head, head)

    def testJqueryAutocompleteJS(self):
        auto = Autocomplete(path='/some/path', maxresults=50, inputs=[('mainsearchinput', 'drilldown.dc.subject')])

        head,body = ''.join(compose(auto.handleRequest(path='/some/path/jquery.autocomplete.js', arguments={}))).split('\r\n'*2,1)

        self.assertTrue('Extending jQuery with autocomplete' in body, body[:300])
        self.assertTrue('Content-Type: application/x-javascript' in head, head)

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