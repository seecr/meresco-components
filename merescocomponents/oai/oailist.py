## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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

from merescocore.framework.observable import Observable

from resumptiontoken import resumptionTokenFromString, ResumptionToken
from oaitool import ISO8601, ISO8601Exception
from oairecordverb import OaiRecordVerb
from itertools import chain

BATCH_SIZE = 200

class OaiList(OaiRecordVerb, Observable):
    """4.3 ListIdentifiers
Summary and Usage Notes

This verb is an abbreviated form of ListRecords, retrieving only headers rather than records. Optional arguments permit selective harvesting of headers based on set membership and/or datestamp. Depending on the repository's support for deletions, a returned header may have a status attribute of "deleted" if a record matching the arguments specified in the request has been deleted.
Arguments

    * from an optional argument with a UTCdatetime value, which specifies a lower bound for datestamp-based selective harvesting.
    * until an optional argument with a UTCdatetime value, which specifies a upper bound for datestamp-based selective harvesting.
    * metadataPrefix a required argument, which specifies that headers should be returned only if the metadata format matching the supplied metadataPrefix is available or, depending on the repository's support for deletions, has been deleted. The metadata formats supported by a repository and for a particular item can be retrieved using the ListMetadataFormats request.
    * set an optional argument with a setSpec value , which specifies set criteria for selective harvesting.
    * resumptionToken an exclusive argument with a value that is the flow control token returned by a previous ListIdentifiers request that issued an incomplete list.

Error and Exception Conditions

    * badArgument - The request includes illegal arguments or is missing required arguments.
    * badResumptionToken - The value of the resumptionToken argument is invalid or expired.
    * cannotDisseminateFormat - The value of the metadataPrefix argument is not supported by the repository.
    * noRecordsMatch- The combination of the values of the from, until, and set arguments results in an empty list.
    * noSetHierarchy - The repository does not support sets.

4.5 ListRecords
Summary and Usage Notes

This verb is used to harvest records from a repository. Optional arguments permit selective harvesting of records based on set membership and/or datestamp. Depending on the repository's support for deletions, a returned header may have a status attribute of "deleted" if a record matching the arguments specified in the request has been deleted. No metadata will be present for records with deleted status.
Arguments

    * from an optional argument with a UTCdatetime value, which specifies a lower bound for datestamp-based selective harvesting.
    * until an optional argument with a UTCdatetime value, which specifies a upper bound for datestamp-based selective harvesting.
    * set an optional argument with a setSpec value , which specifies set criteria for selective harvesting.
    * resumptionToken an exclusive argument with a value that is the flow control token returned by a previous ListRecords request that issued an incomplete list.
    * metadataPrefix a required argument (unless the exclusive argument resumptionToken is used) that specifies the metadataPrefix of the format that should be included in the metadata part of the returned records. Records should be included only for items from which the metadata format
      matching the metadataPrefix can be disseminated. The metadata formats supported by a repository and for a particular item can be retrieved using the ListMetadataFormats request.

Error and Exception Conditions

    * badArgument - The request includes illegal arguments or is missing required arguments.
    * badResumptionToken - The value of the resumptionToken argument is invalid or expired.
    * cannotDisseminateFormat - The value of the metadataPrefix argument is not supported by the repository.
    * noRecordsMatch - The combination of the values of the from, until, set and metadataPrefix arguments results in an empty list.
    * noSetHierarchy - The repository does not support sets.
"""
    def __init__(self):
        OaiRecordVerb.__init__(self, ['ListIdentifiers', 'ListRecords'], {
            'from': 'optional',
            'until': 'optional',
            'set': 'optional',
            'resumptionToken': 'exclusive',
            'metadataPrefix': 'required'})
        Observable.__init__(self)

    def listRecords(self, webRequest):
        self.startProcessing(webRequest)

    def listIdentifiers(self, webRequest):
        self.startProcessing(webRequest)

    def preProcess(self, webRequest):
        if self._resumptionToken:
            token = resumptionTokenFromString(self._resumptionToken)
            if not token:
                return self.writeError(webRequest, "badResumptionToken")
            self._continueAt = token._continueAt
            self._metadataPrefix = token._metadataPrefix
            self._from = token._from
            self._until = token._until
            self._set = token._set
        else:
            self._continueAt = '0'
            try:
                self._from = self._from and ISO8601(self._from)
                self._until  = self._until and ISO8601(self._until)
                if self._from and self._until:
                    if self._from.isShort() != self._until.isShort():
                        return self.writeError(webRequest, 'badArgument', 'from and/or until arguments must match in length')
                    if str(self._from) > str(self._until):
                        return self.writeError(webRequest, 'badArgument', 'from argument must be smaller than until argument')
                self._from = self._from and self._from.floor()
                self._until = self._until and self._until.ceil()
            except ISO8601Exception, e:
                return self.writeError(webRequest, 'badArgument', 'from and/or until arguments are faulty')

        if not self._metadataPrefix in [prefix for prefix, na, na in self.any.getAllPrefixes()]:
            return self.writeError(webRequest, 'cannotDisseminateFormat')

        result = self.any.oaiSelect(
            sets=self._set and [self._set] or None,
            prefix=self._metadataPrefix,
            continueAt=self._continueAt,
            oaiFrom=self._from,
            oaiUntil=self._until)
        try:
            firstRecord = result.next()
            self._queryRecordIds = chain(iter([firstRecord]), result)
        except StopIteration:
            self._queryRecordIds = iter([])
            self.writeError(webRequest, 'noRecordsMatch')

    def process(self, webRequest):
        for i, id in enumerate(self._queryRecordIds):
            if i == BATCH_SIZE:
                webRequest.write('<resumptionToken>%s</resumptionToken>' % ResumptionToken(
                    self._metadataPrefix,
                    self.any.getUnique(prevId),
                    self._from,
                    self._until,
                    self._set))
                return
            self.writeRecord(webRequest, id, self._verb == "ListRecords")
            prevId = id

        if self._resumptionToken:
            webRequest.write('<resumptionToken/>')
