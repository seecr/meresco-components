## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.core.observable import Observable
from traceback import format_exc
from xml.sax.saxutils import escape as escapeXml
from meresco.components.xml_generic.validate import ValidateException

from sys import stderr

from meresco.core import Observable
from meresco.components.xml_generic import ValidateException
from meresco.components.xmlxpath import lxmlElementUntail

from xml.sax.saxutils import escape as escapeXml
from traceback import format_exc, print_exc
from lxml.etree import parse, XMLSyntaxError, ElementTree
from StringIO import StringIO
from meresco.xml.namespaces import xpath, namespaces, xpathFirst

class SruRecordUpdate(Observable):
    def __init__(self, name=None, stderr=stderr, sendRecordData=True):
        Observable.__init__(self, name=name)
        self._stderr=stderr
        self._sendRecordData = sendRecordData

    def handleRequest(self, Body="", **kwargs):
        yield '\r\n'.join(['HTTP/1.0 200 Ok', 'Content-Type: text/xml; charset=utf-8\r\n', ''])
        if not Body:
            yield self._respond(
                diagnosticUri='info:srw/diagnostic/12/9',
                details='Update request lacks a record in its body.',
                message='Missing mandatory element:  record rejected')
            return

        try:
            try:
                lxmlNode = parse(StringIO(Body))
            except XMLSyntaxError:
                print_exc(file=self._stderr)
                print >> self._stderr, Body
                self._stderr.flush()
                raise
            updateRequest = xpathFirst(lxmlNode, '/*[local-name()="updateRequest"]')
            recordId = xpathFirst(updateRequest, 'ucp:recordIdentifier/text()')
            if recordId is None or recordId.strip() == '':
                raise ValueError("recordIdentifier is mandatory.")
            recordId = str(recordId)
            action = xpathFirst(updateRequest, 'ucp:action/text()')
            action = action.partition("info:srw/action/1/")[-1]
            if action in ['create', 'replace']:
                record = xpathFirst(updateRequest, 'srw:record')
                lxmlNode = record
                if self._sendRecordData:
                    lxmlNode = xpathFirst(record, 'srw:recordData/child::*')
                recordSchema = xpathFirst(record, 'srw:recordSchema/text()')
                yield self.all.add(
                        identifier=recordId,
                        partname=recordSchema,
                        lxmlNode=ElementTree(lxmlElementUntail(lxmlNode)),
                    )
            elif action == 'delete':
                yield self.all.delete(identifier=recordId)
            else:
                raise ValueError("action value should refer to either 'create', 'replace' or 'delete'.")
            yield self._respond()
        except ValidateException, e:
            yield self._respond(
                diagnosticUri='info:srw/diagnostic/12/12',
                details=escapeXml(str(e)),
                message='Invalid data:  record rejected')
        except Exception, e:
            yield self._respond(
                diagnosticUri='info:srw/diagnostic/12/1',
                details=escapeXml(format_exc()),
                message='Invalid component:  record rejected')

    def _respond(self, diagnosticUri=None, details='', message=''):
        operationStatus = "success"
        diagnostics = ""
        if diagnosticUri:
            operationStatus = "fail"
            uri = diagnosticUri
            diagnostics = DIAGNOSTIC_XML % locals()
        yield RESPONSE_XML % locals()


RESPONSE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>%(operationStatus)s</ucp:operationStatus>%(diagnostics)s
</srw:updateResponse>"""

DIAGNOSTIC_XML = """<srw:diagnostics>
    <diag:diagnostic xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/">
        <diag:uri>%(uri)s</diag:uri>
        <diag:details>%(details)s</diag:details>
        <diag:message>%(message)s</diag:message>
    </diag:diagnostic>
</srw:diagnostics>"""

class SRURecordUpdate(SruRecordUpdate):
    def __init__(self, *args, **kwargs):
        from warnings import warn
        warn("Please use SruRecordUpdate", DeprecationWarning)
        SruRecordUpdate.__init__(self, *args, **kwargs)

