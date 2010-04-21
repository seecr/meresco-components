## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
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
from unittest import TestCase

from meresco.components.logobserver import LogObserver
from cStringIO import StringIO
from cq2utils.calltrace import CallTrace
from meresco.core.observable import Observable

class LogObserverTest(TestCase):

    def testLogging(self):
        stream = StringIO()
        log = LogObserver(stream)

        class AnArgument:
            def __str__(self):
                return 'Looking for an argument.'
        argument = AnArgument()
        log.unknown('methodName', 'one', argument, 'three')

        time, line = stream.getvalue().split('\t',1)
        self.assertEquals('methodName - one\tLooking for an argument.\tthree\n', line)

    def testLoggingBySubclassing(self):
        stream = StringIO()
        arguments = []
        class MyLogObserver(LogObserver):
            def toString(self, *args):
                arguments.append(args)
                return 'toString'
        log = MyLogObserver(stream)

        log.unknown('methodName', 'one', 'two')

        time, line = stream.getvalue().split('\t',1)
        self.assertEquals('methodName - toString\n', line)
        self.assertEquals([('one','two')], arguments)

    def testLogException(self):
        class B:
            def b(self): raise Exception('B')
        class A(Observable):
            def a(self):
                try:
                    self.any.b()
                except Exception, e:
                    self.do.logException(e)
        a = A()
        stream = StringIO()
        log = LogObserver(stream)
        a.addObserver(B())
        a.addObserver(log)
        a.a()
        lines = stream.getvalue().split('\n')
        self.assertTrue('Traceback (most recent call last):' in lines[0], lines[0])
        self.assertTrue('/logobservertest.py",' in lines[1], lines[1])
        self.assertTrue('    self.any.b()' in lines[2], lines[2])
        self.assertTrue('/logobservertest.py", line ' in lines[3], lines[3])
        self.assertTrue("    def b(self): raise Exception('B')" in lines[4], lines[4])
        self.assertTrue('Exception: B' in lines[5], lines[5])
        self.assertEquals('', lines[6])
        self.assertEquals(7, len(lines))
