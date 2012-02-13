## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
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

from os.path import join, dirname, abspath
from cStringIO import StringIO
from lxml.etree import parse, _ElementTree

from weightless.core import compose, be
from meresco.core import Observable
from meresco.components.xml_generic.validate import Validate, ValidateException
from meresco.components.xml_generic import  __file__ as xml_genericpath


xsd = join(abspath(dirname(xml_genericpath)), 'schemas-lom', 'lomCc.xsd')

class ValidateTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.validate = Validate(xsd)
        self.interceptor = CallTrace('interceptor', returnValues={
            'all_unknown': (x for x in ['done']),
            'any_unknown': (x for x in ['done']),
            'do_unknown': None,
            'call_unknown': 'done',
            'logException': None}, onlySpecifiedMethods=True)
        self.validate.addObserver(self.interceptor)
        self.observable = Observable()
        self.observable.addObserver(self.validate)

    def testValid(self):
        validXml = '<lom xmlns="http://ltsc.ieee.org/xsd/LOM"/>'
        self.assertEquals(['done'], list(compose(self.observable.all.someMethod(parse(StringIO(validXml))))))
        self.assertEquals(['done'], list(compose(self.observable.any.someMethod(parse(StringIO(validXml))))))

        self.interceptor.calledMethods.reset()
        self.observable.do.someMethod(parse(StringIO(validXml)))
        self.assertEquals(['do_unknown'], [m.name for m in self.interceptor.calledMethods])

        self.interceptor.calledMethods.reset()
        self.assertEquals('done', self.observable.call.someMethod(parse(StringIO(validXml))))

    def testInvalid(self):
        invalidXml = '<lom xmlns="http://ltsc.ieee.org/xsd/LOM_this_should_not_work"/>'
        try:
            list(compose(self.observable.any.someMethod(parse(StringIO(invalidXml)))))
            self.fail('must raise exception')
        except ValidateException:
            pass
        self.assertEquals(['logException'], [m.name for m in self.interceptor.calledMethods])
        exception = self.interceptor.calledMethods[0].args[0]
        self.assertTrue("ERROR:SCHEMASV:SCHEMAV_CVC_ELT_1: Element '{http://ltsc.ieee.org/xsd/LOM_this_should_not_work}lom': No matching global declaration available for the validation root." in str(exception), str(exception))
        self.assertTrue("1 %s" % invalidXml in str(exception), str(exception))

        self.assertRaises(ValidateException, lambda: list(compose(self.observable.all.someMethod(parse(StringIO(invalidXml))))))
        self.assertRaises(ValidateException, lambda: list(compose(self.observable.do.someMethod(parse(StringIO(invalidXml))))))
        self.assertRaises(ValidateException, lambda: list(compose(self.observable.call.someMethod(parse(StringIO(invalidXml))))))

    def testAssertInvalidString(self):
        invalid = '<OAI-PMH/>'
        try:
            list(compose(self.observable.any.message(parse(StringIO(invalid)))))
            self.fail('must raise exception')
        except ValidateException, e:
            pass
        self.assertEquals(['logException'], [m.name for m in self.interceptor.calledMethods])
        exception = self.interceptor.calledMethods[0].args[0]
        self.assertTrue("ERROR:SCHEMASV:SCHEMAV_CVC_ELT_1: Element 'OAI-PMH': No matching global declaration available for the validation root." in str(exception), str(exception))
        self.assertTrue("1 <OAI-PMH/>" in str(exception), str(exception))

    def testTransparencyInCaseOfNoAnyAndCallResponders(self):
        observer = CallTrace('observer', returnValues={
            'f': (i for i in [42]),
            'g': 42
        })
        root = be((Observable(),
            (Validate(xsd),),
            (observer,)
        ))

        self.assertEquals([42], list(compose(root.any.f())))
        self.assertEquals(42, root.call.g())

