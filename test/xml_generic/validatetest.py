## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
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

from cStringIO import StringIO
from cq2utils.cq2testcase import CQ2TestCase

from lxml.etree import parse, _ElementTree

from meresco.components.xml_generic.validate import Validate, ValidateException
from meresco.core import Observable

from weightless.core import compose

from meresco.components.xml_generic import  __file__ as xml_genericpath
from os.path import join, dirname, abspath

class ValidateTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.validate = Validate(join(abspath(dirname(xml_genericpath)), 'schemas-lom', 'lomCc.xsd'))
        self.exception = None
        self.args = None
        class Interceptor:
            def all_unknown(inner, message, *args, **kwargs):
                self.args = args
                yield None
            def any_unknown(inner, message, *args, **kwargs):
                self.args = args
                return 'sync_any'
            def logException(inner, anException):
                self.exception = anException

        self.validate.addObserver(Interceptor())
        self.observable = Observable()
        self.observable.addObserver(self.validate)

    # async too!
    def testOneInvalid(self):
        invalidXml = '<lom xmlns="http://ltsc.ieee.org/xsd/LOM_this_should_not_work"/>'
        try:
            list(compose(self.observable.any.someMethod(parse(StringIO(invalidXml)))))
            self.fail('must raise exception')
        except ValidateException:
            pass
        self.assertTrue("ERROR:SCHEMASV:SCHEMAV_CVC_ELT_1: Element '{http://ltsc.ieee.org/xsd/LOM_this_should_not_work}lom': No matching global declaration available for the validation root." in str(self.exception), str(self.exception))
        self.assertTrue("1 %s" % invalidXml in str(self.exception), str(self.exception))

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
        self.assertTrue("ERROR:SCHEMASV:SCHEMAV_CVC_ELT_1: Element 'OAI-PMH': No matching global declaration available for the validation root." in str(self.exception), str(self.exception))
        self.assertTrue("1 <OAI-PMH/>" in str(self.exception), str(self.exception))

