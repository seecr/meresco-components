## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
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
from xml.sax.saxutils import escape as xmlEscape

from meresco.core import Observable
from meresco.components.http import utils as httputils

from cqlparser import parseString, CQLParseException, CQLTokenizerException

from weightless.core import compose

from diagnostic import DIAGNOSTIC
from diagnostic import GENERAL_SYSTEM_ERROR, SYSTEM_TEMPORARILY_UNAVAILABLE, UNSUPPORTED_OPERATION, UNSUPPORTED_VERSION, UNSUPPORTED_PARAMETER_VALUE, MANDATORY_PARAMETER_NOT_SUPPLIED, UNSUPPORTED_PARAMETER, QUERY_FEATURE_UNSUPPORTED

DEFAULT_VERSION = '1.1'
SUPPORTED_VERSIONS = ['1.1', '1.2']
DEFAULT_MAXIMUMRECORDS = '10'

XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'

OFFICIAL_REQUEST_PARAMETERS = {
    'explain': ['operation', 'version', 'stylesheet', 'extraRequestData', 'recordPacking'],
    'searchRetrieve': ['version','query','startRecord','maximumRecords','recordPacking','recordSchema',
'recordXPath','resultSetTTL','sortKeys','stylesheet','extraRequestData','operation']}

MANDATORY_PARAMETERS = {
    'explain':['version', 'operation'],
    'searchRetrieve':['version', 'operation', 'query']}

SUPPORTED_OPERATIONS = ['explain', 'searchRetrieve']


RESPONSE_HEADER = """<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/">
"""

RESPONSE_FOOTER = """</srw:searchRetrieveResponse>"""

DIAGNOSTICS = """%s%s%s<srw:diagnostics>%s</srw:diagnostics>%s""" % (RESPONSE_HEADER, '<srw:version>%s</srw:version>' % DEFAULT_VERSION, '<srw:numberOfRecords>0</srw:numberOfRecords>', DIAGNOSTIC, RESPONSE_FOOTER)


class SruException(Exception):

    def __init__(self, (code, message), details="No details available"):
        Exception.__init__(self, details)
        self.code = code
        self.message = message
        self.details = details

class SruMandatoryParameterNotSuppliedException(SruException):
    def __init__(self, parameterName):
        SruException.__init__(self,
            MANDATORY_PARAMETER_NOT_SUPPLIED,
            details="MANDATORY parameter '%s' not supplied or empty" % parameterName)

class SruParser(Observable):

    def __init__(self, host='', port=0, description='Meresco SRU', modifiedDate='1970-01-01T00:00:00Z', database=None, defaultRecordSchema="dc", defaultRecordPacking="xml", maximumMaximumRecords=None):
        Observable.__init__(self)
        self._host = host
        self._port = port
        self._description = description
        self._modifiedDate = modifiedDate
        self._database = database
        self._defaultRecordSchema = defaultRecordSchema
        self._defaultRecordPacking = defaultRecordPacking
        self._maximumMaximumRecords = maximumMaximumRecords

    def handleRequest(self, arguments, **kwargs):
        yield httputils.okXml

        yield XML_HEADER
        try:
            operation, arguments = self._parseArguments(arguments)
            operationMethod = self._explain
            if operation == 'searchRetrieve':
                operationMethod = self._searchRetrieve
            for data in compose(operationMethod(arguments)):
                yield data
        except SruException, e:
            yield DIAGNOSTICS % (e.code, xmlEscape(e.details), xmlEscape(e.message))
            raise StopIteration()
        except Exception, e:
            from traceback import print_exc
            print_exc()
            yield "Unexpected Exception:\n"
            yield str(e)
            raise e

    def _searchRetrieve(self, arguments):
        sruArgs = self.parseSruArgs(arguments)
        arguments.update(sruArgs)
        return self.any.searchRetrieve(**arguments)

    def parseSruArgs(self, arguments):
        sruArgs = {
            'version': arguments['version'][0],
            'operation': arguments['operation'][0],
            'recordSchema': arguments.get('recordSchema', [self._defaultRecordSchema])[0],
            'recordPacking': arguments.get('recordPacking', [self._defaultRecordPacking])[0],
        }
        startRecord = arguments.get('startRecord', ['1'])[0]
        if not startRecord.isdigit() or int(startRecord) < 1:
            raise SruException(UNSUPPORTED_PARAMETER_VALUE, 'startRecord')
        sruArgs['startRecord'] = int(startRecord)

        maximumRecords = arguments.get('maximumRecords', [DEFAULT_MAXIMUMRECORDS])[0]
        if not maximumRecords.isdigit() or int(maximumRecords) < 0:
            raise SruException(UNSUPPORTED_PARAMETER_VALUE, 'maximumRecords')
        sruArgs['maximumRecords'] = int(maximumRecords)
        if self._maximumMaximumRecords and sruArgs['maximumRecords'] > self._maximumMaximumRecords:
            raise SruException(UNSUPPORTED_PARAMETER_VALUE, 'maximumRecords > %s' % self._maximumMaximumRecords)

        query = arguments.get('query', [''])[0]
        try:
            parseString(query)
        except CQLParseException, e:
            raise SruException(QUERY_FEATURE_UNSUPPORTED, str(e))
        except CQLTokenizerException, e:
            raise SruException(QUERY_FEATURE_UNSUPPORTED, str(e))
        sruArgs['query'] = query

        if 'sortKeys' in arguments :
            try:
                sortBy, ignored, sortDirection = arguments.get('sortKeys')[0].split(',')
                sruArgs['sortBy'] = sortBy.strip()
                sruArgs['sortDescending'] = bool(int(sortDirection))
            except ValueError:
                pass

        for key in arguments:
            if not key in sruArgs:
                sruArgs[key.replace('-', '_')] = arguments[key]

        return sruArgs


    def _parseArguments(self, arguments):
        if arguments == {}:
            arguments = {'version':[DEFAULT_VERSION], 'operation':['explain']}
        operation = arguments.get('operation', [None])[0]
        self._validateArguments(operation, arguments)
        return operation, arguments

    def _validateArguments(self, operation, arguments):
        if operation == None:
            raise SruException(MANDATORY_PARAMETER_NOT_SUPPLIED, 'operation')

        if not operation in SUPPORTED_OPERATIONS:
            raise SruException(UNSUPPORTED_OPERATION, operation)

        self._validateCorrectEncoding(arguments)

        for argument in arguments:
            if not (argument in OFFICIAL_REQUEST_PARAMETERS[operation] or argument.startswith('x-')):
                raise SruException(UNSUPPORTED_PARAMETER, argument)

        for argument in MANDATORY_PARAMETERS[operation]:
            if not argument in arguments:
                raise SruException(MANDATORY_PARAMETER_NOT_SUPPLIED, argument)

        if not arguments['version'][0] in SUPPORTED_VERSIONS:
            raise SruException(UNSUPPORTED_VERSION, arguments['version'][0])

    def _validateCorrectEncoding(self, arguments):
        try:
            for key, values in arguments.items():
                key.decode('utf-8')
                for value in values:
                    value.decode('utf-8')
        except UnicodeDecodeError:
            raise SruException(UNSUPPORTED_PARAMETER_VALUE, "Parameters are not properly 'utf-8' encoded.")

    def _explain(self, arguments):
        version = arguments['version'][0]
        host = self._host
        port = self._port
        description = self._description
        modifiedDate = self._modifiedDate
        database = self._database
        yield """<srw:explainResponse xmlns:srw="http://www.loc.gov/zing/srw/"
   xmlns:zr="http://explain.z3950.org/dtd/2.0/">
    <srw:version>%(version)s</srw:version>
    <srw:record>
        <srw:recordPacking>xml</srw:recordPacking>
        <srw:recordSchema>http://explain.z3950.org/dtd/2.0/</srw:recordSchema>
        <srw:recordData>
            <zr:explain>
                <zr:serverInfo wsdl="http://%(host)s:%(port)s/%(database)s" protocol="SRU" version="%(version)s">
                    <host>%(host)s</host>
                    <port>%(port)s</port>
                    <database>%(database)s</database>
                </zr:serverInfo>
                <zr:databaseInfo>
                    <title lang="en" primary="true">SRU Database</title>
                    <description lang="en" primary="true">%(description)s</description>
                </zr:databaseInfo>
                <zr:metaInfo>
                    <dateModified>%(modifiedDate)s</dateModified>
                </zr:metaInfo>
            </zr:explain>
        </srw:recordData>
    </srw:record>
</srw:explainResponse>""" % locals()

    def searchRetrieve(self, *args, **kwargs):
        return self.any.searchRetrieve(*args, **kwargs)
