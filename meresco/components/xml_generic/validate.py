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

from lxml.etree import parse, XMLSchema, XMLSchemaParseError, _ElementTree, tostring
from StringIO import StringIO

from meresco.core import Observable, fakeGenerator

class ValidateException(Exception):
    pass

class Validate(Observable):
    def __init__(self, schemaPath):
        Observable.__init__(self)
        try:
            self._schema = XMLSchema(parse(open(schemaPath)))
        except XMLSchemaParseError, e:
            print e.error_log.last_error
            raise


    def all_unknown(self, message, *args, **kwargs):
        self._detectAndValidate(*args, **kwargs)
        yield self.all.unknown(message, *args, **kwargs)

    def do_unknown(self, message, *args, **kwargs):
        self._detectAndValidate(*args, **kwargs)
        return self.do.unknown(message, *args, **kwargs)

    def any_unknown(self, message, *args, **kwargs):
        self._detectAndValidate(*args, **kwargs)
        response = yield self.any.unknown(message, *args, **kwargs)
        raise StopIteration(response)

    def call_unknown(self, message, *args, **kwargs):
        self._detectAndValidate(*args, **kwargs)
        return self.call.unknown(message, *args, **kwargs)

    def _detectAndValidate(self, *args, **kwargs):
        allArguments = list(args) + kwargs.values()
        for arg in allArguments:
            if type(arg) == _ElementTree:
                self._schema.validate(arg)
                if self._schema.error_log:
                    exception = ValidateException(formatException(self._schema, arg))
                    self.do.logException(exception)
                    raise exception


def assertValid(xmlString, schemaPath):
    schema = XMLSchema(parse(open(schemaPath)))
    toValidate = parse(StringIO(xmlString))
    schema.validate(toValidate)
    if schema.error_log:
        raise AssertionError(formatException(schema, toValidate))

def formatException(schema, lxmlNode):
    message = str(schema.error_log.last_error) + "\n\n"
    for nr, line in enumerate(tostring(lxmlNode, encoding="utf-8", pretty_print=True).split('\n')):
        message += "%s %s\n" % (nr+1, line)
    return message
