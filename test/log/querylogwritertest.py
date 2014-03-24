## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2014 Stichting Kennisnet http://www.kennisnet.nl
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
from meresco.components.log import QueryLogWriter

class QueryLogWriterTest(SeecrTestCase):

    def testLoggedPaths(self):
        log = CallTrace('log')
        writer = QueryLogWriter(log=log, loggedPaths=['/sru', '/srw'])
        writer.writeLog(**defaultKwargs(path=['/sru']))
        writer.writeLog(**defaultKwargs(path=['/srv']))
        writer.writeLog(**defaultKwargs(path=['/srw.php']))
        self.assertEquals(['log','log'], log.calledMethodNames())
        self.assertEquals(['/sru', '/srw.php'], [m.kwargs['path'] for m in log.calledMethods])

    def testLogAllPaths(self):
        log = CallTrace('log')
        writer = QueryLogWriter(log=log)
        writer.writeLog(**defaultKwargs(path=['/sru']))
        writer.writeLog(**defaultKwargs(path=['/srv']))
        writer.writeLog(**defaultKwargs(path=['/srw.php']))
        self.assertEquals(['log','log', 'log'], log.calledMethodNames())
        self.assertEquals(['/sru', '/srv', '/srw.php'], [m.kwargs['path'] for m in log.calledMethods])

def defaultKwargs(**kwargs):
    result = dict(
        timestamp=[1257161136.0],
        path=['/sru'],
        Client=[('11.22.33.44', 1234)],
        responseSize=[5432],
        duration=[3.0],
        sruArguments=[{'version':'1.2'}],
        sruNumberOfRecords=[32],
    )
    result.update(**kwargs)
    return result
