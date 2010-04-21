## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from xml.sax.saxutils import quoteattr, escape as xmlEscape

from meresco.core import Observable, decorate, decorateWith
from meresco.components.drilldown import DRILLDOWN_HEADER, DRILLDOWN_FOOTER

from cqlparser import parseString as parseCQL
from weightless import compose

from sruparser import VERSION, DIAGNOSTICS, DIAGNOSTIC, GENERAL_SYSTEM_ERROR, QUERY_FEATURE_UNSUPPORTED, RESPONSE_HEADER, RESPONSE_FOOTER

ECHOED_PARAMETER_NAMES = ['version', 'query', 'startRecord', 'maximumRecords', 'recordPacking', 'recordSchema', 'recordXPath', 'resultSetTTL', 'sortKeys', 'stylesheet', 'x-recordSchema']

class SruHandler(Observable):
    def searchRetrieve(self, version=None, recordSchema=None, recordPacking=None, startRecord=1, maximumRecords=10, query='', sortBy=None, sortDescending=False, **kwargs):
        SRU_IS_ONE_BASED = 1

        start = startRecord - SRU_IS_ONE_BASED
        cqlAbstractSyntaxTree = parseCQL(query)
        try:
            total, recordIds = self.any.executeCQL(
                cqlAbstractSyntaxTree=cqlAbstractSyntaxTree,
                start=start,
                stop=start + maximumRecords,
                sortBy=sortBy,
                sortDescending=sortDescending,
                **kwargs)
        except Exception, e:
            yield DIAGNOSTICS % ( QUERY_FEATURE_UNSUPPORTED[0], QUERY_FEATURE_UNSUPPORTED[1], xmlEscape(str(e)))
            return
        yield self._startResults(total)

        recordsWritten = 0
        for recordId in recordIds:
            if not recordsWritten:
                yield '<srw:records>'
            yield self._writeResult(recordSchema=recordSchema, recordPacking=recordPacking, recordId=recordId, **kwargs)
            recordsWritten += 1

        if recordsWritten:
            yield '</srw:records>'
            nextRecordPosition = start + recordsWritten
            if nextRecordPosition < total:
                yield '<srw:nextRecordPosition>%i</srw:nextRecordPosition>' % (nextRecordPosition + SRU_IS_ONE_BASED)

        yield self._writeEchoedSearchRetrieveRequest(version=version, recordSchema=recordSchema, recordPacking=recordPacking, startRecord=startRecord, maximumRecords=maximumRecords, query=query, sortBy=sortBy, sortDescending=sortDescending, **kwargs)
        yield self._writeExtraResponseData(cqlAbstractSyntaxTree=cqlAbstractSyntaxTree, version=version, recordSchema=recordSchema, recordPacking=recordPacking, startRecord=startRecord, maximumRecords=maximumRecords, query=query, sortBy=sortBy, sortDescending=sortDescending, **kwargs)
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
        return decorate('<srw:extraResponseData>',
            self._extraResponseDataTryExcept(cqlAbstractSyntaxTree=cqlAbstractSyntaxTree, **kwargs),
            '</srw:extraResponseData>')

    def _extraResponseDataTryExcept(self, cqlAbstractSyntaxTree=None, **kwargs):
        try:
            stuffs = compose(self.all.extraResponseData(cqlAbstractSyntaxTree=cqlAbstractSyntaxTree, **kwargs))
            for stuff in stuffs:
                yield stuff
        except Exception, e:
            yield DIAGNOSTIC % tuple(GENERAL_SYSTEM_ERROR + [xmlEscape(str(e))])

    def _startResults(self, numberOfRecords):
        yield RESPONSE_HEADER
        yield '<srw:version>%s</srw:version>' % VERSION
        yield '<srw:numberOfRecords>%s</srw:numberOfRecords>' % numberOfRecords

    def _endResults(self):
        yield RESPONSE_FOOTER

    def _writeResult(self, recordSchema=None, recordPacking=None, recordId=None, **kwargs):
        yield '<srw:record>'
        yield '<srw:recordSchema>%s</srw:recordSchema>' % recordSchema
        yield '<srw:recordPacking>%s</srw:recordPacking>' % recordPacking
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


    def _writeExtraRecordData(self, x_recordSchema=None, recordPacking=None, recordId=None, **kwargs):
        if not x_recordSchema:
            raise StopIteration()

        yield '<srw:extraRecordData>'
        for schema in x_recordSchema:
            yield '<recordData recordSchema="%s">' % xmlEscape(schema)
            yield self._catchErrors(self._yieldRecordForRecordPacking(recordId, schema, recordPacking), schema, recordId)
            yield '</recordData>'
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
