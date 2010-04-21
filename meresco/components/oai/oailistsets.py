## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
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

from oairecordverb import OaiRecordVerb
from meresco.core.observable import Observable

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

        self._queryResult = self.any.getAllSets()
        if len(self._queryResult) == 0:
            return self.writeError(webRequest, 'noSetHierarchy')

    def process(self, webRequest):

        webRequest.write(''.join('<set><setSpec>%s</setSpec><setName>set %s</setName></set>' % (setSpec, setSpec) for setSpec in self._queryResult))

        if self._resumptionToken:
            webRequest.write('<resumptionToken/>')

