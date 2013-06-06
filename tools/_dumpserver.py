## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009, 2011 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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


from glob import glob
from sys import path, argv, exit
for directory in glob('../deps.d/*'):
    path.insert(0, directory)
path.insert(0, '..')

from weightless.core import be, compose
from weightless.io import Reactor
from sys import stdout
from os.path import abspath, dirname, join, isdir, basename
from os import makedirs
from meresco.components.http import ObservableHttpServer
from meresco.components.sru.srurecordupdate import RESPONSE_XML, DIAGNOSTIC_XML, escapeXml
from meresco.core import Observable
from re import compile
from traceback import format_exc
from lxml.etree import XML, tostring
from meresco.xml import xpath, xpathFirst

mydir = dirname(abspath(__file__))
notWordCharRE = compile('\W+')




class Dump(object):
    def __init__(self, dumpdir, maxCount=10):
        self._dumpdir = dumpdir
        self._number = self._findLastNumber()
        self._maxCountNumber = self._number + maxCount
        self._maxCount = maxCount

    def handleRequest(self, Body='', **kwargs):
        yield '\r\n'.join(['HTTP/1.0 200 Ok', 'Content-Type: text/xml; charset=utf-8\r\n', ''])
        try:
            updateRequest = xpathFirst(XML(Body), '/ucp:updateRequest')
            recordId = xpathFirst(updateRequest, 'ucp:recordIdentifier/text()')
            normalizedRecordId = notWordCharRE.sub('_', recordId)
            self._number +=1
            if self._number <= self._maxCountNumber:
                filename = '%05d_%s.updateRequest' %(self._number, normalizedRecordId)
                with open(join(self._dumpdir, filename), 'w') as f:
                    print recordId
                    stdout.flush()
                    f.write(tostring(updateRequest))
                answer = RESPONSE_XML % {
                    "operationStatus": "success",
                    "diagnostics": ""}
            else:
                self._maxCountNumber = self._number + self._maxCount
                print 'Reached maxCount'
                answer = RESPONSE_XML % {
                    "operationStatus": "fail",
                    "diagnostics": DIAGNOSTIC_XML % {'uri': '', 'message': '', 'details': escapeXml("Enough is enough")}}
        except Exception, e:
            answer = RESPONSE_XML % {
                "operationStatus": "fail",
                "diagnostics": DIAGNOSTIC_XML % {'uri': '', 'message': '', 'details': escapeXml(format_exc())}}

        yield answer

    def _findLastNumber(self):
        return max([int(basename(f)[:5]) for f in glob(join(self._dumpdir, '*.updateRequest'))]+[0])


def main(reactor, portNumber, dumpdir):
    isdir(dumpdir) or makedirs(dumpdir)
    server = be(
        (Observable(),
            (ObservableHttpServer(reactor, portNumber),
                (Dump(dumpdir),)
            )
        )
    )
    list(compose(server.once.observer_init()))

if __name__== '__main__':
    args = argv[1:]
    if len(args) != 2:
        print "Usage %s <portnumber> <dumpdir>" % argv[0]
        exit(1)
    portNumber = int(args[0])
    dumpdir = args[1]
    reactor = Reactor()
    main(reactor, portNumber, dumpdir)
    print 'Ready to rumble the dumpserver at', portNumber
    print '  - dumps are written to', dumpdir
    stdout.flush()
    reactor.loop()
