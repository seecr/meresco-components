## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012, 2018 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
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

from lxml.etree import parse, XMLSchema, XMLSchemaParseError, _ElementTree, XML
from io import StringIO

from weightless.core import NoneOfTheObserversRespond, DeclineMessage
from meresco.core import Observable
from meresco.components import lxmltostring

class ValidateException(Exception):
    pass

class Validate(Observable):
    def __init__(self, schemaPath):
        Observable.__init__(self)
        try:
            with open(schemaPath) as fp:
                self._schema = XMLSchema(parse(fp))
        except XMLSchemaParseError as e:
            print(e.error_log.last_error)
            raise


    def all_unknown(self, message, *args, **kwargs):
        self._detectAndValidate(*args, **kwargs)
        yield self.all.unknown(message, *args, **kwargs)

    def do_unknown(self, message, *args, **kwargs):
        self._detectAndValidate(*args, **kwargs)
        return self.do.unknown(message, *args, **kwargs)

    def any_unknown(self, message, *args, **kwargs):
        self._detectAndValidate(*args, **kwargs)
        try:
            response = yield self.any.unknown(message, *args, **kwargs)
            return response
        except NoneOfTheObserversRespond:
            raise DeclineMessage

    def call_unknown(self, message, *args, **kwargs):
        self._detectAndValidate(*args, **kwargs)
        try:
            return self.call.unknown(message, *args, **kwargs)
        except NoneOfTheObserversRespond:
            raise DeclineMessage

    def _detectAndValidate(self, *args, **kwargs):
        allArguments = list(args) + list(kwargs.values())
        for arg in allArguments:
            if type(arg) == _ElementTree:
                self.validate(arg)

    def validate(self, arg):
        self._schema.validate(arg)
        if self._schema.error_log:
            exception = ValidateException(formatException(self._schema, arg))
            self.do.logException(exception)
            raise exception

    def assertValid(self, xmlOrString):
        toValidate = XML(xmlOrString.encode('utf-8')) if isinstance(xmlOrString, str) else xmlOrString
        self._schema.validate(toValidate)
        if self._schema.error_log:
            raise AssertionError(formatException(self._schema, toValidate))

def assertValid(xmlString, schemaPath):
    Validate(schemaPath).assertValid(xmlString)

def formatException(schema, lxmlNode):
    message = str(schema.error_log.last_error) + "\n\n"
    for nr, line in enumerate(lxmltostring(lxmlNode, pretty_print=True).split('\n')):
        message += "%s %s\n" % (nr+1, line)
    return message
