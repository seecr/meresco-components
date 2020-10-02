## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015-2016 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015-2017 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import consume

from meresco.components.log.packettolog import PacketToLog

class PacketToLogTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.packetToLog = PacketToLog()
        self.observer = CallTrace('observer', emptyGeneratorMethods=['logData'])
        self.packetToLog.addObserver(self.observer)

    def testAdd(self):
        consume(self.packetToLog.add(data=LOGDATA))
        self.assertEqual(['logData'], self.observer.calledMethodNames())
        self.assertEqual({'dataDict': RESULTDATA}, self.observer.calledMethods[0].kwargs)


LOGDATA='1257161136 11.12.13.14 4.0K 12.340 0 /path key=value'
RESULTDATA={
    'timestamp': 1257161136,
    'ipAddress': '11.12.13.14',
    'size': 4096,
    'duration': 12340,
    'hits': 0,
    'path': '/path',
    'arguments': 'key=value',
}
