## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011-2012 Stichting Kennisnet http://www.kennisnet.nl
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

from xml.sax.saxutils import quoteattr, escape as xmlEscape

from meresco.core import Observable, decorate
from meresco.components.drilldown import DRILLDOWN_HEADER, DRILLDOWN_FOOTER, DEFAULT_MAXIMUM_TERMS
from meresco.components.sru.sruparser import SruException
from weightless.core import compose, Yield

from cqlparser import parseString as parseCQL
from warnings import warn

from time import time
from decimal import Decimal
from traceback import print_exc

from diagnostic import createDiagnostic, DIAGNOSTIC, GENERAL_SYSTEM_ERROR, QUERY_FEATURE_UNSUPPORTED, UNSUPPORTED_PARAMETER_VALUE
from sruparser import DIAGNOSTICS, RESPONSE_HEADER, RESPONSE_FOOTER

ECHOED_PARAMETER_NAMES = ['version', 'query', 'startRecord', 'maximumRecords', 'recordPacking', 'recordSchema', 'recordXPath', 'resultSetTTL', 'sortKeys', 'stylesheet']

millis = Decimal('0.001')

class SruHandler(Observable):
    def __init__(self, extraRecordDataNewStyle=True, drilldownSortedByTermCount=False, extraXParameters=None, includeQueryTimes=False, querySuggestionsCount=0, drilldownMaximumMaximumResults=None):
        Observable.__init__(self)
        self._drilldownSortedByTermCount = drilldownSortedByTermCount
        self._extraRecordDataNewStyle = extraRecordDataNewStyle
        self._extraXParameters = set(extraXParameters or [])
        self._extraXParameters.add("x-recordSchema")
        self._includeQueryTimes = includeQueryTimes
        self._querySuggestionsCount = querySuggestionsCount
        self._drilldownMaximumMaximumResults = drilldownMaximumMaximumResults

    def searchRetrieve(self, version=None, recordSchema=None, recordPacking=None, startRecord=1, maximumRecords=10, query='', sruArguments=None, diagnostics=None, **kwargs):
        SRU_IS_ONE_BASED = 1

        limitBeyond = kwargs.get('limitBeyond', None)

        t0 = self._timeNow()
        start = startRecord - SRU_IS_ONE_BASED
        cqlAbstractSyntaxTree = parseCQL(query)

        drilldownFieldnamesAndMaximums = None
        if 'x-term-drilldown' in sruArguments:
            drilldownFieldnamesAndMaximums = self._parseDrilldownArgs(sruArguments['x-term-drilldown'])
        suggestionsQuery = None
        if 'x-suggestionsQuery' in sruArguments:
            suggestionsQuery = sruArguments['x-suggestionsQuery'][0]

        extraArguments = dict((key, value) for key, value in sruArguments.items() if key.startswith('x-'))
        try:
            response = yield self.any.executeQuery(
                    cqlAbstractSyntaxTree=cqlAbstractSyntaxTree,
                    start=start,
                    stop=start + maximumRecords,
                    fieldnamesAndMaximums=drilldownFieldnamesAndMaximums,
                    suggestionsCount=self._querySuggestionsCount,
                    suggestionsQuery=suggestionsQuery,
                    extraArguments=extraArguments,
                    **kwargs)
            total, recordIds = response.total, response.hits
            drilldownData = getattr(response, "drilldownData", None)
        except Exception, e:
            print_exc()
            yield createDiagnostic(uri=QUERY_FEATURE_UNSUPPORTED[0], message=QUERY_FEATURE_UNSUPPORTED[1], details=xmlEscape(str(e)))
            return

        queryTime = str(self._timeNow() - t0)

        yield self._startResults(total, version)

        recordsWritten = 0
        for recordId in recordIds:
            if not recordsWritten:
                yield '<srw:records>'
            yield self._writeResult(recordSchema=recordSchema, recordPacking=recordPacking, recordId=recordId, version=version, sruArguments=sruArguments, **kwargs)
            recordsWritten += 1

        if recordsWritten:
            yield '</srw:records>'
            nextRecordPosition = start + recordsWritten
            if nextRecordPosition < total and (limitBeyond == None or (limitBeyond != None and limitBeyond > nextRecordPosition)):
                yield '<srw:nextRecordPosition>%i</srw:nextRecordPosition>' % (nextRecordPosition + SRU_IS_ONE_BASED)

        yield self._writeEchoedSearchRetrieveRequest(sruArguments=sruArguments)
        yield self._writeDiagnostics(diagnostics=diagnostics)
        yield self._writeExtraResponseData(cqlAbstractSyntaxTree=cqlAbstractSyntaxTree, version=version, recordSchema=recordSchema, recordPacking=recordPacking, startRecord=startRecord, maximumRecords=maximumRecords, query=query, drilldownData=drilldownData, response=response, queryTime=queryTime, suggestionsQuery=suggestionsQuery, sruArguments=sruArguments, **kwargs)
        yield self._endResults()

    def _writeEchoedSearchRetrieveRequest(self, sruArguments, **kwargs):
        yield '<srw:echoedSearchRetrieveRequest>'
        for paramSets in ECHOED_PARAMETER_NAMES, self._extraXParameters:
            for parameterName in paramSets:
                value = sruArguments.get(parameterName, [])
                for v in (value if isinstance(value, list) else [value]):
                    aValue = xmlEscape(str(v))
                    yield '<srw:%(parameterName)s>%(aValue)s</srw:%(parameterName)s>' % locals()
        for chunk in decorate('<srw:extraRequestData>', compose(self.all.echoedExtraRequestData(sruArguments=sruArguments, **kwargs)), '</srw:extraRequestData>'):
            yield chunk
        yield '</srw:echoedSearchRetrieveRequest>'

    def _writeDiagnostics(self, diagnostics):
        if not diagnostics:
            return
        yield '<srw:diagnostics>'
        for code, message, details in diagnostics:
            yield createDiagnostic(uri=code, message=xmlEscape(message), details=xmlEscape(details))
        yield '</srw:diagnostics>'

    def _writeExtraResponseData(self, response=None, queryTime=None, **kwargs):
        result = compose(self._extraResponseDataTryExcept(response=response, queryTime=queryTime, **kwargs))
        headerWritten = False

        if self._includeQueryTimes:    
            headerWritten = True
            t_sru_ms = Decimal(queryTime).quantize(millis)
            if hasattr(response, "queryTime"):
                t_index_ms = (Decimal(response.queryTime)/1000).quantize(millis)
            else:
                t_index_ms = -1

            yield """<srw:extraResponseData>
        <querytimes xmlns="http://meresco.org/namespace/timing">
            <sru>PT%(sru)sS</sru>
            <index>PT%(index)sS</index>
        </querytimes>
    """ % {'sru': t_sru_ms, 'index': t_index_ms}

        for line in result:
            if line is Yield or callable(line):
                yield line
                continue
            if line and not headerWritten:
                yield '<srw:extraResponseData>'
                headerWritten = True
            yield line
        if headerWritten:
            yield '</srw:extraResponseData>'

    def _extraResponseDataTryExcept(self, **kwargs):
        try:
            yield self.all.extraResponseData(**kwargs)
        except Exception, e:
            yield createDiagnostic(uri=GENERAL_SYSTEM_ERROR[0], message=GENERAL_SYSTEM_ERROR[1], details=xmlEscape(str(e)))

    def _startResults(self, numberOfRecords, version):
        yield RESPONSE_HEADER
        yield '<srw:version>%s</srw:version>' % version 
        yield '<srw:numberOfRecords>%s</srw:numberOfRecords>' % numberOfRecords

    def _endResults(self):
        yield RESPONSE_FOOTER

    def _writeResult(self, recordSchema=None, recordPacking=None, recordId=None, version=None, **kwargs):
        yield '<srw:record>'
        yield '<srw:recordSchema>%s</srw:recordSchema>' % xmlEscape(recordSchema)
        yield '<srw:recordPacking>%s</srw:recordPacking>' % xmlEscape(recordPacking)
        if version == "1.2": 
            yield '<srw:recordIdentifier>%s</srw:recordIdentifier>' % xmlEscape(recordId)
        yield self._writeRecordData(recordSchema=recordSchema, recordPacking=recordPacking, recordId=recordId)
        yield self._writeExtraRecordData(recordPacking=recordPacking, recordId=recordId, **kwargs)
        yield '</srw:record>'

    def _writeRecordData(self, recordSchema=None, recordPacking=None, recordId=None):
        yield '<srw:recordData>'
        yield self._catchErrors(self._yieldRecordForRecordPacking(recordId=recordId, recordSchema=recordSchema, recordPacking=recordPacking), recordSchema, recordId)
        yield '</srw:recordData>'

    def _catchErrors(self, dataGenerator, recordSchema, recordId):
        try:
            yield dataGenerator
        except IOError, e:
            yield createDiagnostic(uri=GENERAL_SYSTEM_ERROR[0], message=GENERAL_SYSTEM_ERROR[1], details=xmlEscape("recordSchema '%s' for identifier '%s' does not exist" % (recordSchema, recordId)))
        except Exception, e:
            yield createDiagnostic(uri=GENERAL_SYSTEM_ERROR[0], message=GENERAL_SYSTEM_ERROR[1], details=xmlEscape(str(e)))

    def _writeOldStyleExtraRecordData(self, schema, recordPacking, recordId):
        yield '<recordData recordSchema="%s">' % xmlEscape(schema)
        yield self._catchErrors(self._yieldRecordForRecordPacking(recordId, schema, recordPacking), schema, recordId)
        yield '</recordData>'

    def _writeExtraRecordData(self, sruArguments=None, recordPacking=None, recordId=None, **kwargs):
        if not 'x-recordSchema' in sruArguments:
            raise StopIteration()

        yield '<srw:extraRecordData>'
        for schema in sruArguments['x-recordSchema']:
            if not self._extraRecordDataNewStyle:
                yield self._writeOldStyleExtraRecordData(schema, recordPacking, recordId)
                continue
            yield '<srw:record>'
            yield '<srw:recordSchema>%s</srw:recordSchema>' % xmlEscape(schema)
            yield '<srw:recordPacking>%s</srw:recordPacking>' % recordPacking
            yield '<srw:recordData>'
            yield self._catchErrors(self._yieldRecordForRecordPacking(recordId, schema, recordPacking), schema, recordId)
            yield '</srw:recordData>'
            yield '</srw:record>'
        yield '</srw:extraRecordData>'

    def _yieldRecordForRecordPacking(self, recordId=None, recordSchema=None, recordPacking=None):
        generator = compose(self.all.yieldRecord(identifier=recordId, partname=recordSchema))
        if recordPacking == 'xml':
            yield generator
            return
        if recordPacking == 'string':
            for data in generator:
                if data is Yield or callable(data):
                    yield data
                else:
                    yield xmlEscape(data)
        else:
            raise Exception("Unknown Record Packing: %s" % recordPacking)

    def _parseDrilldownArgs(self, x_term_drilldown):
        if x_term_drilldown == None or len(x_term_drilldown) != 1:
            return

        def splitTermAndMaximum(field):
            maxTerms = DEFAULT_MAXIMUM_TERMS if self._drilldownMaximumMaximumResults is None else min(DEFAULT_MAXIMUM_TERMS, self._drilldownMaximumMaximumResults)
            splitted = field.rsplit(":", 1)
            if len(splitted) == 2:
                try:
                    field, maxTerms = splitted[0], int(splitted[1])
                    if self._drilldownMaximumMaximumResults is not None:
                        if maxTerms > self._drilldownMaximumMaximumResults:
                            raise SruException(UNSUPPORTED_PARAMETER_VALUE, '%s; drilldown with maximumResults > %s' % (field, self._drilldownMaximumMaximumResults))
                        elif maxTerms < 1:
                            raise SruException(UNSUPPORTED_PARAMETER_VALUE, '%s; drilldown with maximumResults < 1' % field)
                except ValueError:
                    pass
            return field, maxTerms, self._drilldownSortedByTermCount

        return [splitTermAndMaximum(field) for field in x_term_drilldown[0].split(",")]

    def _timeNow(self):
        return time()
