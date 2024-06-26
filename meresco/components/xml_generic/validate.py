## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012, 2018, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from lxml.etree import parse, XMLSchema, XMLSchemaParseError, _ElementTree, XML, XMLParser, Resolver
from io import StringIO

from weightless.core import NoneOfTheObserversRespond, DeclineMessage
from meresco.core import Observable
from meresco.components import lxmltostring

from meresco.components import usrSharePath
import pathlib

class ValidateException(Exception):
    pass

class XSD_Resolver(Resolver):
    def __init__(self):
        self._xsd_path = pathlib.Path(usrSharePath) / "xsd" / "schemas"

    def resolve(self, url, id, context):
        _, fname = url.rsplit("/", 1)
        xsd_filename = self._xsd_path / fname
        if xsd_filename.is_file():
            return self.resolve_filename(xsd_filename.as_posix(), context)
        return Resolver.resolve(self, url, id, context)


class Validate(Observable):
    def __init__(self, schemaPath):
        Observable.__init__(self)
        self._parser = XMLParser()
        self._parser.resolvers.add(XSD_Resolver())

        try:
            with open(schemaPath) as fp:
                self._schema = XMLSchema(parse(fp, self._parser))
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
