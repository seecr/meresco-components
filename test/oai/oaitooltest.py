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

from merescocomponents.oai.oaitool import ISO8601Exception, ISO8601
from merescocomponents.oai.oaiverb import OaiVerb
from cq2utils.cq2testcase import CQ2TestCase
from cq2utils.calltrace import CallTrace

class OaiToolTest(CQ2TestCase):
    
    def testWriteRequestArgs(self):
        getHost = CallTrace("getHost")
        getHost.port = 8000
        request = CallTrace("Request")
        request.returnValues['getHost'] = getHost
        request.returnValues['getRequestHostname'] = 'localhost'
        request.path = '/oai'
    
        verb = OaiVerb(None, None)
        request.args = {'identifier': ['with a "']}
        verb.writeRequestArgs(request)
        
        writeCall = request.calledMethods[-1]
        self.assertEquals('write', writeCall.name)
        self.assertEquals('<request identifier="with a &quot;">http://localhost:8000/oai</request>', writeCall.arguments[0])
        
    def testISO8601(self):
        """http://www.w3.org/TR/NOTE-datetime
   Below is the complete spec by w3. OAI-PMH only allows for 
   YYYY-MM-DD and
   YYYY-MM-DDThh:mm:ssZ
   
   Year:
      YYYY (eg 1997)
   Year and month:
      YYYY-MM (eg 1997-07)
   Complete date:
      YYYY-MM-DD (eg 1997-07-16)
   Complete date plus hours and minutes:
      YYYY-MM-DDThh:mmTZD (eg 1997-07-16T19:20+01:00)
   Complete date plus hours, minutes and seconds:
      YYYY-MM-DDThh:mm:ssTZD (eg 1997-07-16T19:20:30+01:00)
   Complete date plus hours, minutes, seconds and a decimal fraction of a
second
      YYYY-MM-DDThh:mm:ss.sTZD (eg 1997-07-16T19:20:30.45+01:00)"""
        
        def right(s):
            ISO8601(s)
        
        def wrong(s):
            try:
                ISO8601(s)
                self.fail()
            except ISO8601Exception, e:
                pass
            
        wrong('2000')
        wrong('2000-01')
        right('2000-01-01')
        wrong('aaaa-bb-cc')
        wrong('2000-01-32')
        wrong('2000-01-01T00:00Z')
        right('2000-01-01T00:00:00Z')
        right('2000-12-31T23:59:59Z')
        wrong('2000-01-01T00:00:61Z')
        wrong('2000-01-01T00:00:00+01:00')
        wrong('2000-01-01T00:00:00.000Z')
        
        iso8601 = ISO8601('2000-01-01T00:00:00Z')
        self.assertFalse(iso8601.isShort())
        self.assertEquals('2000-01-01T00:00:00Z', str(iso8601))
        self.assertEquals('2000-01-01T00:00:00Z', iso8601.floor())
        self.assertEquals('2000-01-01T00:00:00Z', iso8601.ceil())
        
        iso8601 = ISO8601('2000-01-01')
        self.assertTrue(iso8601.isShort())
        self.assertEquals('2000-01-01T00:00:00Z', str(iso8601))
        self.assertEquals('2000-01-01T00:00:00Z', iso8601.floor())
        self.assertEquals('2000-01-01T23:59:59Z', iso8601.ceil())
