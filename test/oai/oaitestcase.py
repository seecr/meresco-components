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

from cq2utils.cq2testcase import CQ2TestCase

from lxml.etree import parse, XMLSchema, XMLSchemaParseError, tostring
from cq2utils.calltrace import CallTrace
from meresco.core.observable import Observable
from StringIO import StringIO
from os.path import join, dirname, abspath
from glob import glob

from meresco.components.xml_generic import  __file__ as xml_genericpath


class OaiTestCase(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.observable = Observable()
        self.subject = self.getSubject()
        self.subject.getTime = lambda : '2007-02-07T00:00:00Z'
        self.observable.addObserver(self.subject)
        self.request = CallTrace('Request')
        self.request.path = '/path/to/oai'
        self.request.getRequestHostname = lambda: 'server'
        class Host:
            def __init__(self):
                self.port = '9000'
        self.request.getHost = lambda: Host()
        self.stream = StringIO()
        self.request.write = self.stream.write

    OAIPMH = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
         http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
<responseDate>2007-02-07T00:00:00Z</responseDate>
%s
</OAI-PMH>"""

    def assertValidString(self, aXmlString):
        schema = getSchema()
        tree = parse(StringIO(aXmlString))
        schema.validate(tree)
        if schema.error_log:
            for nr, line in enumerate(aXmlString.split('\n')):
                print nr+1, line
            self.fail(schema.error_log.last_error)

schemaLocation = join(abspath(dirname(__file__)), 'schemas')

rootSchema = '<?xml version="1.0" encoding="utf-8"?><schema targetNamespace="http://www.meresco.org/XML" \
            xmlns="http://www.w3.org/2001/XMLSchema" \
            elementFormDefault="qualified">\n' \
 + '\n'.join('<import namespace="%s" schemaLocation="%s"/>' %
    (parse(xsd).getroot().get('targetNamespace'), xsd)
        for xsd in glob(join(schemaLocation,'*.xsd'))) \
+ '</schema>'

schemaXml = parse(StringIO(rootSchema))

schema = None

def getSchema():
    global schema
    if not schema:
        try:
            schema = XMLSchema(schemaXml)
        except XMLSchemaParseError, e:
            print e.error_log.last_error
            raise
    return schema
