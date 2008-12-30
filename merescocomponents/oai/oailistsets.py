## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
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

from oairecordverb import OaiRecordVerb
from meresco.framework.observable import Observable

class OaiListSets(OaiRecordVerb, Observable):
    """4.6 ListSets
Summary and Usage Notes

This verb is used to retrieve the set structure of a repository, useful for selective harvesting.
Arguments

    * resumptionToken an exclusive argument with a value that is the flow control token returned by a previous ListSets request that issued an incomplete list.

Error and Exception Conditions

    * badArgument - The request includes illegal arguments or is missing required arguments.
    * badResumptionToken - The value of the resumptionToken argument is invalid or expired.
    * noSetHierarchy - The repository does not support sets."""

    def __init__(self):
        OaiRecordVerb.__init__(self, ['ListSets'], {'resumptionToken': 'exclusive'})
        Observable.__init__(self)

    def listSets(self, aWebRequest):
        self.startProcessing(aWebRequest)

    def preProcess(self, webRequest):
        if self._resumptionToken:
            return self.writeError(webRequest, 'badResumptionToken')

        self._queryResult = self.any.listSets()
        if len(self._queryResult) == 0:
            return self.writeError(webRequest, 'noSetHierarchy')

    def process(self, webRequest):

        webRequest.write(''.join('<set><setSpec>%s</setSpec></set>' % setSpec for setSpec in self._queryResult))

        if self._resumptionToken:
            webRequest.write('<resumptionToken/>')

