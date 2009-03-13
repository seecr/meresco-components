## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
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

from oaiverb import OaiVerb
from xml.sax.saxutils import escape as escapeXml

class OaiIdentify(OaiVerb):
    """
http://www.openarchives.org/OAI/openarchivesprotocol.html#Identify
4.2 Identify
Summary and Usage Notes

This verb is used to retrieve information about a repository. Some of the information returned is required as part of the OAI-PMH. Repositories may also employ the Identify verb to return additional descriptive information.
Arguments

None
Error and Exception Conditions

    * badArgument - The request includes illegal arguments.

Response Format

The response must include one instance of the following elements:

    * repositoryName : a human readable name for the repository;
    * baseURL : the base URL of the repository;
    * protocolVersion : the version of the OAI-PMH supported by the repository;
    * earliestDatestamp : a UTCdatetime that is the guaranteed lower limit of all datestamps recording changes, modifications, or deletions in the repository. A repository must not use datestamps lower than the one specified by the content of the earliestDatestamp element. earliestDatestamp must be expressed at the finest granularity supported by the repository.
    * deletedRecord : the manner in which the repository supports the notion of deleted records. Legitimate values are no ; transient ; persistent with meanings defined in the section on deletion.
    * granularity: the finest harvesting granularity supported by the repository. The legitimate values are YYYY-MM-DD and YYYY-MM-DDThh:mm:ssZ with meanings as defined in ISO8601.

The response must include one or more instances of the following element:

    * adminEmail : the e-mail address of an administrator of the repository.

The response may include multiple instances of the following optional elements:

    * compression : a compression encoding supported by the repository. The recommended values are those defined for the Content-Encoding header in Section 14.11 of RFC 2616 describing HTTP 1.1. A compression element should not be included for the identity encoding, which is implied.
    * description : an extensible mechanism for communities to describe their repositories. For example, the description container could be used to include collection-level metadata in the response to the Identify request. Implementation Guidelines are available to give directions with this respect. Each description container must be accompanied by the URL of an XML schema describing the structure of the description container.

    """
    def __init__(self, repositoryName = "The Repository Name", adminEmail = 'not available', repositoryIdentifier="www.example.org"):
        OaiVerb.__init__(self, ['Identify'], {})
        self._repositoryName = repositoryName
        self._adminEmail = adminEmail
        self._repositoryIdentifier = repositoryIdentifier

    def identify(self, webRequest):
        self.startProcessing(webRequest)

    def process(self, webRequest):
        values = {
            'repositoryName': escapeXml(self._repositoryName),
            'baseURL': escapeXml(self.getRequestUrl(webRequest)),
            'adminEmails': ''.join([ADMIN_EMAIL % escapeXml(email) for email in [self._adminEmail]]),
            'deletedRecord': 'persistent',
            'repositoryIdentifier': escapeXml(self._repositoryIdentifier)
        }
        values.update(hardcoded_values)
        webRequest.write(IDENTIFY % values)


hardcoded_values = {
    'protocolVersion': '2.0',
    'earliestDatestamp': '1970-01-01T00:00:00Z',
    'granularity': 'YYYY-MM-DDThh:mm:ssZ'
}


REQUEST = """<request verb="Identify">%s</request>"""

ADMIN_EMAIL = """<adminEmail>%s</adminEmail>"""

IDENTIFY = """<repositoryName>%(repositoryName)s</repositoryName>
<baseURL>%(baseURL)s</baseURL>
<protocolVersion>%(protocolVersion)s</protocolVersion>
    %(adminEmails)s
<earliestDatestamp>%(earliestDatestamp)s</earliestDatestamp>
<deletedRecord>%(deletedRecord)s</deletedRecord>
<granularity>%(granularity)s</granularity>
<description>
  <oai-identifier xmlns="http://www.openarchives.org/OAI/2.0/oai-identifier" 
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
      xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai-identifier
      http://www.openarchives.org/OAI/2.0/oai-identifier.xsd">
    <scheme>oai</scheme>
    <repositoryIdentifier>%(repositoryIdentifier)s</repositoryIdentifier>
    <delimiter>:</delimiter>
    <sampleIdentifier>oai:%(repositoryIdentifier)s:5324</sampleIdentifier>
  </oai-identifier>
</description>
"""
