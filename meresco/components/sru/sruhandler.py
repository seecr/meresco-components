## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2016, 2018 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2011-2015, 2018 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012 SURF http://www.surf.nl
# Copyright (C) 2013-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from time import time
from decimal import Decimal
from traceback import print_exc
from xml.sax.saxutils import escape as xmlEscape

from cqlparser import cqlToExpression

from weightless.core import compose, Yield
from meresco.core import Observable, decorate

from meresco.components.drilldown import DEFAULT_MAXIMUM_TERMS
from meresco.components.sru.sruparser import SruException
from meresco.components.log import collectLogForScope
from .diagnostic import createDiagnostic, GENERAL_SYSTEM_ERROR, QUERY_FEATURE_UNSUPPORTED, UNSUPPORTED_PARAMETER_VALUE
from .sruparser import RESPONSE_HEADER, RESPONSE_FOOTER


ECHOED_PARAMETER_NAMES = ['version', 'query', 'startRecord', 'maximumRecords', 'recordPacking', 'recordSchema', 'recordXPath', 'resultSetTTL', 'sortKeys', 'stylesheet']

MILLIS = Decimal('0.001')

DRILLDOWN_SORTBY_INDEX = 'index'
DRILLDOWN_SORTBY_COUNT = 'count'

class SruHandler(Observable):
    def __init__(self, extraRecordDataNewStyle=True, drilldownSortBy=DRILLDOWN_SORTBY_COUNT, extraXParameters=None, includeQueryTimes=False, drilldownMaximumMaximumResults=None, enableCollectLog=False):
        Observable.__init__(self)
        self._drilldownSortBy = drilldownSortBy
        self._extraRecordDataNewStyle = extraRecordDataNewStyle
        self._extraXParameters = set(extraXParameters or [])
        self._extraXParameters.add("x-recordSchema")
        self._includeQueryTimes = includeQueryTimes
        self._drilldownMaximumMaximumResults = drilldownMaximumMaximumResults
        self._drilldownMaximumTerms = DEFAULT_MAXIMUM_TERMS if self._drilldownMaximumMaximumResults is None else min(DEFAULT_MAXIMUM_TERMS, self._drilldownMaximumMaximumResults)
        self._collectLogForScope = collectLogForScope if enableCollectLog else lambda **kwargs: None

    def searchRetrieve(self, version=None, recordPacking=None, startRecord=1, maximumRecords=10, query='', sruArguments=None, diagnostics=None, **kwargs):
        SRU_IS_ONE_BASED = 1

        limitBeyond = kwargs.get('limitBeyond', None)
        localLogCollector = {'arguments': sruArguments}

        try:
            t0 = self._timeNow()
            start = startRecord - SRU_IS_ONE_BASED

            facets = None
            if 'x-term-drilldown' in sruArguments:
                facets = self._parseDrilldownArgs(sruArguments['x-term-drilldown'])

            queryExpression = cqlToExpression(query)

            extraArguments = dict((key, value) for key, value in list(sruArguments.items()) if key.startswith('x-'))
            try:
                response = yield self.any.executeQuery(
                        query=queryExpression,
                        start=start,
                        stop=start + maximumRecords,
                        facets=facets,
                        extraArguments=extraArguments,
                        **kwargs)
                total, hits = response.total, response.hits
                drilldownData = getattr(response, "drilldownData", None)
            except Exception as e:
                print_exc()
                yield RESPONSE_HEADER
                yield self._writeDiagnostics([(QUERY_FEATURE_UNSUPPORTED[0], QUERY_FEATURE_UNSUPPORTED[1], str(e))])
                yield RESPONSE_FOOTER
                return

            queryTime = str(self._timeNow() - t0)

            yield self._startResults(total, version)

            recordsWritten = 0
            for hit in hits:
                if not recordsWritten:
                    yield '<srw:records>'
                yield self._writeResult(recordPacking=recordPacking, hit=hit, version=version, sruArguments=sruArguments, **kwargs)
                recordsWritten += 1

            if recordsWritten:
                yield '</srw:records>'
                nextRecordPosition = start + recordsWritten
                if nextRecordPosition < total and (limitBeyond == None or (limitBeyond != None and limitBeyond > nextRecordPosition)):
                    yield '<srw:nextRecordPosition>%i</srw:nextRecordPosition>' % (nextRecordPosition + SRU_IS_ONE_BASED)

            yield self._writeEchoedSearchRetrieveRequest(sruArguments=sruArguments)
            yield self._writeDiagnostics(diagnostics=diagnostics)
            yield self._writeExtraResponseData(version=version, recordPacking=recordPacking, startRecord=startRecord, maximumRecords=maximumRecords, query=query, drilldownData=drilldownData, response=response, queryTime=queryTime, startTime=t0, sruArguments=sruArguments, localLogCollector=localLogCollector, **kwargs)
            yield self._endResults()
        finally:
            self._collectLogForScope(sru=localLogCollector)

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
            yield self._createDiagnostic(uri=code, message=xmlEscape(message), details=xmlEscape(details))
        yield '</srw:diagnostics>'

    def _writeExtraResponseData(self, response=None, queryTime=None, startTime=None, localLogCollector=None, **kwargs):
        result = compose(self._extraResponseDataTryExcept(response=response, queryTime=queryTime, **kwargs))

        headerWritten = False

        for line in result:
            if line is Yield or callable(line):
                yield line
                continue
            if line and not headerWritten:
                yield '<srw:extraResponseData>'
                headerWritten = True
            yield line

        t_sru_ms = Decimal(str(self._timeNow() - startTime)).quantize(MILLIS)
        t_queryTime_ms = Decimal(queryTime).quantize(MILLIS)
        if hasattr(response, "queryTime"):
            t_index_ms = (Decimal(response.queryTime)/1000).quantize(MILLIS)
        else:
            t_index_ms = -1

        localLogCollector['handlingTime'] = t_sru_ms
        localLogCollector['queryTime'] = t_queryTime_ms
        localLogCollector['indexTime'] = t_index_ms
        localLogCollector['numberOfRecords'] = response.total

        if self._includeQueryTimes:
            if not headerWritten:
                yield '<srw:extraResponseData>'
                headerWritten = True
            queryTimeDict = {'sru': t_sru_ms, 'queryTime': t_queryTime_ms, 'index': t_index_ms}
            yield """
        <querytimes xmlns="http://meresco.org/namespace/timing">
            <sruHandling>PT%(sru)sS</sruHandling>
            <sruQueryTime>PT%(queryTime)sS</sruQueryTime>
            <index>PT%(index)sS</index>
        </querytimes>
    """ % queryTimeDict
            self.do.handleQueryTimes(**queryTimeDict)

        if headerWritten:
            yield '</srw:extraResponseData>'

    def _extraResponseDataTryExcept(self, **kwargs):
        try:
            yield self.all.extraResponseData(**kwargs)
        except Exception as e:
            print_exc()
            yield self._createDiagnostic(uri=GENERAL_SYSTEM_ERROR[0], message=GENERAL_SYSTEM_ERROR[1], details=xmlEscape(str(e)))

    def _startResults(self, numberOfRecords, version):
        yield RESPONSE_HEADER
        yield '<srw:version>%s</srw:version>' % version
        yield '<srw:numberOfRecords>%s</srw:numberOfRecords>' % numberOfRecords

    def _endResults(self):
        yield RESPONSE_FOOTER

    def _writeResult(self, recordSchema=None, recordPacking=None, hit=None, version=None, **kwargs):
        yield '<srw:record>'
        yield '<srw:recordSchema>%s</srw:recordSchema>' % xmlEscape(recordSchema)
        yield '<srw:recordPacking>%s</srw:recordPacking>' % xmlEscape(recordPacking)
        if version == "1.2":
            yield '<srw:recordIdentifier>%s</srw:recordIdentifier>' % xmlEscape(hit.id)
        yield self._writeRecordData(recordSchema=recordSchema, recordPacking=recordPacking, recordId=hit.id)
        yield self._writeExtraRecordData(recordPacking=recordPacking, hit=hit, **kwargs)
        yield '</srw:record>'

    def _writeRecordData(self, recordSchema=None, recordPacking=None, recordId=None):
        yield '<srw:recordData>'
        yield self._catchErrors(self._yieldData(identifier=recordId, recordSchema=recordSchema, recordPacking=recordPacking), recordSchema, recordId)
        yield '</srw:recordData>'

    def _catchErrors(self, dataGenerator, recordSchema, recordId):
        try:
            yield dataGenerator
        except KeyError as e:
            print_exc()
            yield self._createDiagnostic(uri=GENERAL_SYSTEM_ERROR[0], message=GENERAL_SYSTEM_ERROR[1], details=xmlEscape("recordSchema '%s' for identifier '%s' does not exist" % (recordSchema, recordId)))
        except Exception as e:
            print_exc()
            yield self._createDiagnostic(uri=GENERAL_SYSTEM_ERROR[0], message=GENERAL_SYSTEM_ERROR[1], details=xmlEscape(str(e)))

    def _writeOldStyleExtraRecordData(self, schema, recordPacking, recordId):
        yield '<recordData recordSchema="%s">' % xmlEscape(schema)
        yield self._catchErrors(self._yieldData(identifier=recordId, recordSchema=schema, recordPacking=recordPacking), schema, recordId)
        yield '</recordData>'

    def _writeExtraRecordData(self, sruArguments=None, recordPacking=None, hit=None, **kwargs):
        generator = compose(self.all.extraRecordData(hit=hit))

        started = False
        for data in generator:
            if not started:
                yield '<srw:extraRecordData>'
                started = True
            yield data

        for schema in sruArguments.get('x-recordSchema', []):
            if not started:
                yield '<srw:extraRecordData>'
                started = True
            if not self._extraRecordDataNewStyle:
                yield self._writeOldStyleExtraRecordData(schema, recordPacking, hit.id)
                continue
            yield '<srw:record>'
            yield '<srw:recordSchema>%s</srw:recordSchema>' % xmlEscape(schema)
            yield '<srw:recordPacking>%s</srw:recordPacking>' % recordPacking
            yield '<srw:recordData>'
            yield self._catchErrors(self._yieldData(identifier=hit.id, recordSchema=schema, recordPacking=recordPacking), schema, hit.id)
            yield '</srw:recordData>'
            yield '</srw:record>'
        if started:
            yield '</srw:extraRecordData>'

    def _yieldData(self, identifier=None, recordSchema=None, recordPacking=None):
        data = yield self.any.retrieveData(identifier=identifier, name=recordSchema)
        if recordPacking == 'xml':
            yield data
        elif recordPacking == 'string':
            yield xmlEscape(data)
        else:
            raise Exception("Unknown Record Packing: %s" % recordPacking)

    def _parseDrilldownArgs(self, x_term_drilldown):
        if x_term_drilldown == None or len(x_term_drilldown) < 1:
            return

        def splitTermAndMaximum(request):
            result = dict(fieldname=request, maxTerms=self._drilldownMaximumTerms, sortBy=self._drilldownSortBy)
            splitted = request.rsplit(":", 1)
            if len(splitted) == 2:
                try:
                    result['fieldname'], result['maxTerms'] = splitted[0], int(splitted[1])
                    if self._drilldownMaximumMaximumResults is not None:
                        if result['maxTerms'] > self._drilldownMaximumMaximumResults:
                            raise SruException(UNSUPPORTED_PARAMETER_VALUE, '%s; drilldown with maximumResults > %s' % (result['fieldname'], self._drilldownMaximumMaximumResults))
                        elif result['maxTerms'] < 1:
                            raise SruException(UNSUPPORTED_PARAMETER_VALUE, '%s; drilldown with maximumResults < 1' % result['fieldname'])
                except ValueError:
                    pass
            return result

        def parseRequest(request):
            return splitTermAndMaximum(request)
        return [parseRequest(singleRequest) for request in x_term_drilldown for singleRequest in request.split(",") if singleRequest.strip()]

    def _createDiagnostic(self, uri, message, details):
        additionalDiagnosticDetails = compose(self.all.additionalDiagnosticDetails())
        print("additionalDiagnosticDetails", additionalDiagnosticDetails)
        details = ' - '.join([details] + list(additionalDiagnosticDetails))
        return createDiagnostic(uri=uri, message=message, details=details)

    def _timeNow(self):
        return time()
