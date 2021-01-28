## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011 Seecr http://seecr.nl
# Copyright (C) 2011-2012, 2014, 2018, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012-2014, 2018, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2013 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
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

from xml.sax.saxutils import escape as xmlEscape

from meresco.core import Observable
from meresco.components.http import utils as httputils
from meresco.xml import namespaces

from cqlparser import parseString, CQLParseException, CQLTokenizerException

from weightless.core import compose

from .diagnostic import DIAGNOSTIC
from .diagnostic import UNSUPPORTED_OPERATION, UNSUPPORTED_VERSION, UNSUPPORTED_PARAMETER_VALUE, MANDATORY_PARAMETER_NOT_SUPPLIED, UNSUPPORTED_PARAMETER, QUERY_FEATURE_UNSUPPORTED

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


RESPONSE_HEADER = """<srw:searchRetrieveResponse %(xmlns_srw)s %(xmlns_diag)s %(xmlns_xcql)s %(xmlns_dc)s %(xmlns_meresco_srw)s>""" % namespaces

RESPONSE_FOOTER = """</srw:searchRetrieveResponse>"""

DIAGNOSTICS = """%s%s%s<srw:diagnostics>%s</srw:diagnostics>%s""" % (RESPONSE_HEADER, '<srw:version>%s</srw:version>' % DEFAULT_VERSION, '<srw:numberOfRecords>0</srw:numberOfRecords>', DIAGNOSTIC, RESPONSE_FOOTER)


class SruException(Exception):

    def __init__(self, xxx_todo_changeme, details="No details available"):
        (code, message) = xxx_todo_changeme
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
    CHANGEABLE_ATTRIBUTES = {'defaultRecordSchema', 'defaultRecordPacking', 'host', 'port', 'description', 'database', 'modifiedDate', 'maximumMaximumRecords'}

    def __init__(self, host=None, port=None, description='Meresco SRU', modifiedDate=None, database=None, defaultRecordSchema="dc", defaultRecordPacking="xml", maximumMaximumRecords=None, wsdl=None, oldAndWrongStyleSortKeys=False):
        Observable.__init__(self)
        self._host = host
        self._port = port
        self._description = description
        self._modifiedDate = modifiedDate
        self._database = database
        self._defaultRecordSchema = defaultRecordSchema
        self._defaultRecordPacking = defaultRecordPacking
        self._maximumMaximumRecords = maximumMaximumRecords
        self._wsdl = wsdl
        self._oldAndWrongStyleSortKeys = oldAndWrongStyleSortKeys


    def setAttribute(self, key, value):
        if key in self.CHANGEABLE_ATTRIBUTES:
            setattr(self, '_'+key, value)

    def handleRequest(self, arguments, **kwargs):
        yield httputils.okXml

        yield XML_HEADER
        try:
            operation, arguments = self._parseArguments(arguments)
            operationMethod = self._explain
            if operation == 'searchRetrieve':
                operationMethod = self._searchRetrieve
            yield operationMethod(arguments, **kwargs)
        except SruException as e:
            additionalDiagnosticDetails = compose(self.all.additionalDiagnosticDetails())
            details = ' - '.join([e.details] + list(additionalDiagnosticDetails))
            yield DIAGNOSTICS % (e.code, xmlEscape(details), xmlEscape(e.message))
            return
        except Exception as e:
            from traceback import print_exc
            print_exc()
            yield "Unexpected Exception:\n"
            yield str(e)
            raise e

    def _searchRetrieve(self, arguments, **kwargs):
        sruArgs, queryArgs = self.parseSruArgs(arguments)
        yield self.all.searchRetrieve(sruArguments=sruArgs, **queryArgs)

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
        except CQLParseException as e:
            raise SruException(QUERY_FEATURE_UNSUPPORTED, str(e))
        except CQLTokenizerException as e:
            raise SruException(QUERY_FEATURE_UNSUPPORTED, str(e))
        sruArgs['query'] = query
        queryArgs = sruArgs.copy()

        if 'sortKeys' in arguments :
            try:
                sortBy, ignored, sortDirection = arguments.get('sortKeys')[0].split(',')
                sortDescending = not bool(int(sortDirection))
                if self._oldAndWrongStyleSortKeys:
                    sortDescending = not sortDescending
                queryArgs['sortKeys'] = [{'sortBy': sortBy.strip(), 'sortDescending': sortDescending}]
                sruArgs['sortKeys'] = arguments['sortKeys']
            except ValueError:
                pass

        for key in arguments:
            if not key in sruArgs:
                sruArgs[key] = arguments[key]

        return sruArgs, queryArgs


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

        #self._validateCorrectEncoding(arguments)

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

    def _explain(self, arguments, RequestURI, Headers, **kwargs):
        version = arguments['version'][0]
        host = self._host or Headers['Host'].split(':')[0]
        port = self._port or Headers['Host'][len(host) + 1:] or '80'
        database = self._database or RequestURI.lstrip('/').split('?')[0]
        description = self._description
        modifiedDate = self._modifiedDate

        yield """<srw:explainResponse xmlns:srw="http://www.loc.gov/zing/srw/"
   xmlns:zr="http://explain.z3950.org/dtd/2.0/">
    <srw:version>%(version)s</srw:version>
    <srw:record>
        <srw:recordPacking>xml</srw:recordPacking>
        <srw:recordSchema>http://explain.z3950.org/dtd/2.0/</srw:recordSchema>
        <srw:recordData>
            <zr:explain>
                <zr:serverInfo """ % locals()
        if self._wsdl:
            yield """wsdl="%s" """ % self._wsdl
        yield """protocol="SRU" version="%(version)s">
                    <zr:host>%(host)s</zr:host>
                    <zr:port>%(port)s</zr:port>
                    <zr:database>%(database)s</zr:database>
                </zr:serverInfo>
                <zr:databaseInfo>
                    <zr:title lang="en" primary="true">SRU Database</zr:title>
                    <zr:description lang="en" primary="true">%(description)s</zr:description>
                </zr:databaseInfo>""" % locals()
        if modifiedDate:
            yield """
                <zr:metaInfo>
                    <zr:dateModified>%(modifiedDate)s</zr:dateModified>
                </zr:metaInfo>""" % locals()
        yield """
            </zr:explain>
        </srw:recordData>
    </srw:record>
</srw:explainResponse>"""

    def searchRetrieve(self, *args, **kwargs):
        yield self.all.searchRetrieve(*args, **kwargs)
