## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#    Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
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

from amara.binderytools import bind_string
from meresco.core.observable import Observable
from traceback import format_exc
from xml.sax.saxutils import escape as escapeXml
from meresco.components.xml_generic.validate import ValidateException

class SRURecordUpdate(Observable):

    def handleRequest(self, Body='', **kwargs):
        yield '\r\n'.join(['HTTP/1.0 200 Ok', 'Content-Type: text/xml, charset=utf-8\r\n', ''])
        try:
            updateRequest = bind_string(Body).updateRequest
            recordId = str(updateRequest.recordIdentifier)
            prefix = "info:srw/action/1/"
            action = str(updateRequest.action)
            if action == prefix + "replace" or action == prefix + "create":
                record = updateRequest.record
                recordSchema = str(record.recordSchema)
                yield self.asyncdo.add(identifier=recordId, partname=recordSchema, amaraNode=record.recordData.childNodes[0])
            elif action == prefix + "delete":
                yield self.asyncdo.delete(recordId)
            else:
                raise Exception("Unknown action: " + action)
            answer = RESPONSE_XML % {
                "operationStatus": "success",
                "diagnostics": ""}
        except ValidateException, e:
            answer = RESPONSE_XML % {
                "operationStatus": "fail",
                "diagnostics": DIAGNOSTIC_XML % {
                    'uri': 'info:srw/diagnostic/12/12',
                    'details': escapeXml(format_exc()),
                    'message': 'Invalid data:  record rejected'}}
        except Exception, e:
            answer = RESPONSE_XML % {
                "operationStatus": "fail",
                "diagnostics": DIAGNOSTIC_XML % {
                    'uri': 'info:srw/diagnostic/12/1', 
                    'details': escapeXml(format_exc()), 
                    'message': 'Invalid component:  record rejected'}}

        yield answer

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
