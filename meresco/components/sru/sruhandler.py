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
from xml.sax.saxutils import quoteattr, escape as xmlEscape

from meresco.core import Observable, decorate, decorateWith
from meresco.components.drilldown import DRILLDOWN_HEADER, DRILLDOWN_FOOTER

from cqlparser import parseString as parseCQL
from weightless.core import compose
from warnings import warn

from sruparser import DIAGNOSTICS, DIAGNOSTIC, GENERAL_SYSTEM_ERROR, QUERY_FEATURE_UNSUPPORTED, RESPONSE_HEADER, RESPONSE_FOOTER

ECHOED_PARAMETER_NAMES = ['version', 'query', 'startRecord', 'maximumRecords', 'recordPacking', 'recordSchema', 'recordXPath', 'resultSetTTL', 'sortKeys', 'stylesheet', 'x-recordSchema']

class SruHandler(Observable):
    def __init__(self, extraRecordDataNewStyle=False):
        Observable.__init__(self)
        self._extraRecordDataNewStyle = extraRecordDataNewStyle
        if not extraRecordDataNewStyle:
            warn("""Old style extraRecordData is used, this is deprecated and will be removed in the future.""", DeprecationWarning)

    def searchRetrieve(self, version=None, recordSchema=None, recordPacking=None, startRecord=1, maximumRecords=10, query='', sortBy=None, sortDescending=False, **kwargs):
        SRU_IS_ONE_BASED = 1

        start = startRecord - SRU_IS_ONE_BASED
        cqlAbstractSyntaxTree = parseCQL(query)

        try:
            response = yield self.asyncany.executeCQL(
                cqlAbstractSyntaxTree=cqlAbstractSyntaxTree,
                start=start,
                stop=start + maximumRecords,
                sortBy=sortBy,
                sortDescending=sortDescending,
                **kwargs)
            total, recordIds = response.total, response.hits
            drilldowndata = getattr(response, "drilldowndata", None)
            if not drilldowndata:
                docset = self.any.docsetFromQuery(cqlAbstractSyntaxTree=cqlAbstractSyntaxTree)
        except Exception, e:
            yield DIAGNOSTICS % ( QUERY_FEATURE_UNSUPPORTED[0], QUERY_FEATURE_UNSUPPORTED[1], xmlEscape(str(e)))
            return
        yield self._startResults(total, version)

        recordsWritten = 0
        for recordId in recordIds:
            if not recordsWritten:
                yield '<srw:records>'
            yield self._writeResult(recordSchema=recordSchema, recordPacking=recordPacking, recordId=recordId, version=version, **kwargs)
            recordsWritten += 1

        if recordsWritten:
            yield '</srw:records>'
            nextRecordPosition = start + recordsWritten
            if nextRecordPosition < total:
                yield '<srw:nextRecordPosition>%i</srw:nextRecordPosition>' % (nextRecordPosition + SRU_IS_ONE_BASED)

        yield self._writeEchoedSearchRetrieveRequest(version=version, recordSchema=recordSchema, recordPacking=recordPacking, startRecord=startRecord, maximumRecords=maximumRecords, query=query, sortBy=sortBy, sortDescending=sortDescending, **kwargs)
        yield self._writeExtraResponseData(cqlAbstractSyntaxTree=cqlAbstractSyntaxTree, version=version, recordSchema=recordSchema, recordPacking=recordPacking, startRecord=startRecord, maximumRecords=maximumRecords, query=query, sortBy=sortBy, sortDescending=sortDescending, docset=docset, **kwargs)
        yield self._endResults()

    def _writeEchoedSearchRetrieveRequest(self, **kwargs):
        yield '<srw:echoedSearchRetrieveRequest>'
        for parameterName in ECHOED_PARAMETER_NAMES:
            value = kwargs.get(parameterName.replace('-', '_'), [])
            for v in (value if isinstance(value, list) else [value]):
                aValue = xmlEscape(str(v))
                yield '<srw:%(parameterName)s>%(aValue)s</srw:%(parameterName)s>' % locals()
        for chunk in decorate('<srw:extraRequestData>', compose(self.all.echoedExtraRequestData(**kwargs)), '</srw:extraRequestData>'):
            yield chunk
        yield '</srw:echoedSearchRetrieveRequest>'

    def _writeExtraResponseData(self, cqlAbstractSyntaxTree=None, **kwargs):
        response = compose(self._extraResponseDataTryExcept(cqlAbstractSyntaxTree=cqlAbstractSyntaxTree, **kwargs))
        headerWritten = False
        for line in response:
            if callable(line):
                yield line
                continue
            if line and not headerWritten:
                yield '<srw:extraResponseData>'
                headerWritten = True
            yield line
        if headerWritten:
            yield '</srw:extraResponseData>'

    def _extraResponseDataTryExcept(self, cqlAbstractSyntaxTree=None, **kwargs):
        try:
            yield self.all.extraResponseData(cqlAbstractSyntaxTree=cqlAbstractSyntaxTree, **kwargs)
        except Exception, e:
            yield DIAGNOSTIC % tuple(GENERAL_SYSTEM_ERROR + [xmlEscape(str(e))])

    def _startResults(self, numberOfRecords, version):
        yield RESPONSE_HEADER
        yield '<srw:version>%s</srw:version>' % version 
        yield '<srw:numberOfRecords>%s</srw:numberOfRecords>' % numberOfRecords

    def _endResults(self):
        yield RESPONSE_FOOTER

    def _writeResult(self, recordSchema=None, recordPacking=None, recordId=None, version=None, **kwargs):
        yield '<srw:record>'
        yield '<srw:recordSchema>%s</srw:recordSchema>' % recordSchema
        yield '<srw:recordPacking>%s</srw:recordPacking>' % recordPacking
        if version == "1.2": 
            yield '<srw:recordIdentifier>%s</srw:recordIdentifier>' % recordId
        yield self._writeRecordData(recordSchema=recordSchema, recordPacking=recordPacking, recordId=recordId)
        yield self._writeExtraRecordData(recordPacking=recordPacking, recordId=recordId, **kwargs)
        yield '</srw:record>'

    def _writeRecordData(self, recordSchema=None, recordPacking=None, recordId=None):
        yield '<srw:recordData>'
        yield self._catchErrors(self._yieldRecordForRecordPacking(recordId=recordId, recordSchema=recordSchema, recordPacking=recordPacking), recordSchema, recordId)
        yield '</srw:recordData>'

    def _catchErrors(self, dataGenerator, recordSchema, recordId):
        try:
            for stuff in compose(dataGenerator):
                yield stuff
        except IOError, e:
            yield DIAGNOSTIC % tuple(GENERAL_SYSTEM_ERROR + [xmlEscape("recordSchema '%s' for identifier '%s' does not exist" % (recordSchema, recordId))])
        except Exception, e:
            yield DIAGNOSTIC % tuple(GENERAL_SYSTEM_ERROR + [xmlEscape(str(e))])

    def _writeOldStyleExtraRecordData(self, schema, recordPacking, recordId):
        yield '<recordData recordSchema="%s">' % xmlEscape(schema)
        yield self._catchErrors(self._yieldRecordForRecordPacking(recordId, schema, recordPacking), schema, recordId)
        yield '</recordData>'

    def _writeExtraRecordData(self, x_recordSchema=None, recordPacking=None, recordId=None, **kwargs):
        if not x_recordSchema:
            raise StopIteration()

        yield '<srw:extraRecordData>'
        for schema in x_recordSchema:
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
        generator = compose(self.all.yieldRecord(recordId, recordSchema))
        if recordPacking == 'xml':
            for data in generator:
                yield data
        elif recordPacking == 'string':
            for data in generator:
                yield xmlEscape(data)
        else:
            raise Exception("Unknown Record Packing: %s" % recordPacking)
