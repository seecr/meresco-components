## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2012 Stichting Kennisnet http://www.kennisnet.nl
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

from xml.sax.saxutils import escape as xmlEscape
from amara.binderytools import bind_string

from cq2utils.amaraextension import getElements
from meresco.core import Observable
from meresco.components.http import utils as httputils

SOAP_XML_URI = "http://schemas.xmlsoap.org/soap/envelope/"

SOAP_HEADER = """<SOAP:Envelope xmlns:SOAP="http://schemas.xmlsoap.org/soap/envelope/"><SOAP:Body>"""

SOAP_FOOTER = """</SOAP:Body></SOAP:Envelope>"""

SOAP = SOAP_HEADER + "%s" + SOAP_FOOTER

from meresco.components.sru import SruParser
from meresco.components.sru.sruparser import SruException, DIAGNOSTICS, UNSUPPORTED_PARAMETER, UNSUPPORTED_OPERATION

class SoapException(Exception):

    def __init__(self, faultCode, faultString):
        self._faultCode = faultCode
        self._faultString = faultString

    def asSoap(self):
        return """<SOAP:Fault><faultcode>%s</faultcode><faultstring>%s</faultstring></SOAP:Fault>""" % (xmlEscape(self._faultCode), xmlEscape(self._faultString))

class Srw(Observable):

    def __init__(self, defaultRecordSchema=None, defaultRecordPacking=None):
        Observable.__init__(self)
        self._defaultRecordSchema = defaultRecordSchema
        self._defaultRecordPacking = defaultRecordPacking

    def handleRequest(self, Body='', **kwargs):
        try:
            arguments = self._soapXmlToArguments(Body)
            if not 'recordPacking' in arguments and self._defaultRecordPacking:
                arguments['recordPacking'] = [self._defaultRecordPacking]
            if not 'recordSchema' in arguments and self._defaultRecordSchema:
                arguments['recordSchema'] = [self._defaultRecordSchema]

        except SoapException, e:
            yield httputils.serverErrorXml
            yield SOAP % e.asSoap()
            raise StopIteration()

        yield httputils.okXml

        try:
            operation, arguments = self.call._parseArguments(arguments)
            self._srwSpecificValidation(operation, arguments)
            sruArgs, queryArgs = self.call.parseSruArgs(arguments)
        except SruException, e:
            yield SOAP % DIAGNOSTICS % (e.code, xmlEscape(e.details), xmlEscape(e.message))
            raise StopIteration()

        try:
            yield SOAP_HEADER
            yield self.all.searchRetrieve(sruArguments=sruArgs, **queryArgs)
            yield SOAP_FOOTER
        except Exception, e:
            yield "Unexpected Exception:\n"
            yield str(e)
            raise e

    def _soapXmlToArguments(self, body):
        arguments = {}
        try:
            envelope = bind_string(body).Envelope
        except Exception, e:
            raise  SoapException("SOAP:Server.userException", str(e))
        if str(envelope.xmlnsUri) != SOAP_XML_URI:
            raise SoapException("SOAP:VersionMismatch", "The processing party found an invalid namespace for the SOAP Envelope element")

        request = envelope.Body.searchRetrieveRequest
        for elem in getElements(request):
            value = arguments.get(str(elem.localName), [])
            value.append(str(elem))
            arguments[str(elem.localName)] = value
        arguments['operation'] = arguments.get('operation', ['searchRetrieve'])
        return arguments

    def _srwSpecificValidation(self, operation, arguments):
        if operation != 'searchRetrieve':
            raise SruException(UNSUPPORTED_OPERATION, operation)
        if 'stylesheet' in arguments:
            raise SruException(UNSUPPORTED_PARAMETER, 'stylesheet')
