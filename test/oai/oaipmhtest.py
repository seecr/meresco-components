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


from cq2utils import CQ2TestCase, CallTrace
from merescocore.framework import Observable, be
from cStringIO import StringIO

from merescocomponents.oai import OaiPmh
from oaitestcase import OaiTestCase

from lxml.etree import parse
from StringIO import StringIO

def xpath(node, path):
    return '\n'.join(node.xpath(path, namespaces={'oai':"http://www.openarchives.org/OAI/2.0/"}))

class OaiPmhTest(OaiTestCase):

    def getSubject(self):
        oaipmh = OaiPmh(repositoryName='The Repository Name', adminEmail='admin@email.extension')
        self.observer = CallTrace('Observers')
        oaipmh.addObserver(self.observer)
        return oaipmh

    def testIdentify(self):
        self.request.args = {'verb': ['Identify']}
        
        self.observable.do.handleRequest(self.request)
        
        result = self.stream.getvalue()
        self.assertValidString(result)
        self.stream.seek(0)
        response = parse(self.stream)
        self.assertEquals('The Repository Name', xpath(response, '/oai:OAI-PMH/oai:Identify/oai:repositoryName/text()'))
        self.assertEquals('http://server:9000/path/to/oai', xpath(response, '/oai:OAI-PMH/oai:request/text()'))
        self.assertEquals('admin@email.extension', xpath(response, '/oai:OAI-PMH/oai:Identify/oai:adminEmail/text()'))
        self.assertEquals('YYYY-MM-DDThh:mm:ssZ', xpath(response, '/oai:OAI-PMH/oai:Identify/oai:granularity/text()'))
        self.assertEquals('1970-01-01T00:00:00Z', xpath(response, '/oai:OAI-PMH/oai:Identify/oai:earliestDatestamp/text()'))
        self.assertEquals('persistent', xpath(response, '/oai:OAI-PMH/oai:Identify/oai:deletedRecord/text()'))

    def testGetRecordUsesObservers(self):
        self.request.args = {'verb':['GetRecord'], 'metadataPrefix': ['oai_dc'], 'identifier': ['oai:ident']}
        self.observer.returnValues['getAllPrefixes'] = [('oai_dc', 'schema', 'namespace')]
        self.observer.returnValues['isAvailable'] = (True, True)
        self.observer.returnValues['getDatestamp'] = '2008-11-14T15:43:00Z'
        self.observer.ignoredAttributes.append('provenance')
        def write(sink, identifier, partName):
            sink.write('<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:dc="http://purl.org/dc/elements/1.1/" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"/>')
        self.observer.write = write

        self.observable.do.handleRequest(self.request)
        
        result = self.stream.getvalue()
        self.assertValidString(result)
        self.assertEquals(['isDeleted', 'getAllPrefixes', 'isAvailable', 'isDeleted', 'getDatestamp', 'getSets', 'unknown'], [m.name for m in self.observer.calledMethods])
        
    def assertBadArgument(self, arguments, additionalMessage = '', errorCode = "badArgument"):
        self.request.args = arguments

        self.observable.do.handleRequest(self.request)

        self.assertEquals("setHeader('content-type', 'text/xml; charset=utf-8')",  str(self.request.calledMethods[0]))
        result = self.stream.getvalue()
        self.assertTrue('<error code="%s">' % errorCode in result)
        self.assertTrue(additionalMessage in result, 'Expected "%s" in "%s"' %(additionalMessage, result))

        try:
            self.assertValidString(result)
        except Exception, e:
            self.fail("Not a valid string:\n" + result + "\n" + str(e))

    def testNoVerb(self):
        self.assertBadArgument({}, 'No "verb" argument found.')
    
    def testNVerbs(self):
        self.assertBadArgument({'verb': ['ListRecords', 'Indentify']}, 'Argument "verb" may not be repeated.')
        
    def testWrongVerb(self):
        self.assertBadArgument({'verb': ['Nonsense']}, 'Value of the verb argument is not a legal OAI-PMH verb, the verb argument is missing, or the verb argument is repeated.', errorCode='badVerb')

    def testIllegalIdentifyArguments(self):
        self.assertBadArgument({'verb': ['Identify'], 'metadataPrefix': ['oai_dc']}, 'Argument(s) "metadataPrefix" is/are illegal.')

    def testNoArgumentsListRecords(self):
        self.assertBadArgument({'verb': ['ListRecords']}, 'Missing argument(s) "resumptionToken" or "metadataPrefix"')

    def testTokenNotUsedExclusivelyListRecords(self):
        self.assertBadArgument({'verb': ['ListRecords'], 'resumptionToken': ['aToken'], 'from': ['aDate']}, '"resumptionToken" argument may only be used exclusively.')

    def testNeitherTokenNorMetadataPrefixListRecords(self):
        self.assertBadArgument({'verb': ['ListRecords'], 'from': ['aDate']}, 'Missing argument(s) "resumptionToken" or "metadataPrefix"')

    def testNonsenseArgumentsListRecords(self):
        self.assertBadArgument({'verb': ['ListRecords'], 'metadataPrefix': ['aDate'], 'nonsense': ['more nonsense'], 'bla': ['b']}, 'Argument(s) "bla", "nonsense" is/are illegal.')

    def testDoubleArgumentsListRecords(self):
        self.assertBadArgument({'verb':['ListRecords'], 'metadataPrefix': ['oai_dc', '2']}, 'Argument "metadataPrefix" may not be repeated.')

    def testGetRecordNoArgumentsGetRecord(self):
        self.assertBadArgument({'verb': ['GetRecord']}, 'Missing argument(s) "identifier" and "metadataPrefix".')

    def testGetNoMetadataPrefixGetRecord(self):
        self.assertBadArgument({'verb': ['GetRecord'], 'identifier': ['oai:ident']}, 'Missing argument(s) "metadataPrefix".')

    def testGetNoIdentifierArgumentGetRecord(self):
        self.assertBadArgument({'verb': ['GetRecord'], 'metadataPrefix': ['oai_dc']}, 'Missing argument(s) "identifier".')

    def testNonsenseArgumentGetRecord(self):
        self.assertBadArgument({'verb': ['GetRecord'], 'metadataPrefix': ['aPrefix'], 'identifier': ['anIdentifier'], 'nonsense': ['bla']}, 'Argument(s) "nonsense" is/are illegal.')

    def testDoubleArgumentsGetRecord(self):
        self.assertBadArgument({'verb':['GetRecord'], 'metadataPrefix': ['oai_dc'], 'identifier': ['oai:ident', '2']}, 'Argument "identifier" may not be repeated.')

    def testResumptionTokensNotSupportedListSets(self):
        self.assertBadArgument({'verb': ['ListSets'], 'resumptionToken': ['someResumptionToken']}, errorCode = "badResumptionToken")

    def testNonsenseArgumentsListSets(self):
        self.assertBadArgument({'verb': ['ListSets'], 'nonsense': ['aDate'], 'nonsense': ['more nonsense'], 'bla': ['b']}, 'Argument(s) "bla", "nonsense" is/are illegal.')

    def testRottenTokenListRecords(self):
        self.assertBadArgument({'verb': ['ListRecords'], 'resumptionToken': ['someResumptionToken']}, errorCode = "badResumptionToken")

    def testIllegalArgumentsListMetadataFormats(self):
        self.assertBadArgument({'verb': ['ListMetadataFormats'], 'somethingElse': ['illegal']})
