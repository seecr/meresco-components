## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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
from seecr.test.io import stderr_replaced

from types import GeneratorType

from weightless.core import be, compose

from meresco.core import Observable

from meresco.components import PeriodicCall


class PeriodicCallTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.reactor = CallTrace('Reactor')
        self.observer = CallTrace('Observer', emptyGeneratorMethods=['handle'], ignoredAttributes=['observer_init'])
        self.pc = PeriodicCall(reactor=self.reactor, interval=3600, errorInterval=15, name='obs_name')
        self.dna = be((Observable(),
        (self.pc,
            (self.observer,),
        ),
        ))
        list(compose(self.dna.once.observer_init()))

    def testWithoutData(self):
        self.assertEquals('obs_name', self.pc.observable_name())
        self.assertEquals(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods
        self.assertEquals(((0, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

        # addTimer(0, pc._periodicCall)
        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        self.assertEquals(['addProcess'], self.reactor.calledMethodNames())
        addProcess, = self.reactor.calledMethods
        self.assertEquals((1, 0), (len(addProcess.args), len(addProcess.kwargs)))
        thisNext = addProcess.args[0]

        self.reactor.calledMethods.reset()
        self.assertEquals([], self.observer.calledMethodNames())
        thisNext()
        self.assertEquals(['handle'], self.observer.calledMethodNames())
        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        removeProcess, addTimer = self.reactor.calledMethods
        self.assertEquals(((), {}), (removeProcess.args, removeProcess.kwargs))
        self.assertEquals(((3600, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

    def testErrorInterval(self):
        def raiser():
            raise Exception('al')
            yield
        self.observer.methods['handle'] = raiser

        addTimer, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        addProcess, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()

        with stderr_replaced() as err:
            addProcess.args[0]()
            errValue = err.getvalue()
            self.assertTrue('Traceback' in errValue, errValue)
            self.assertTrue('Exception: al' in errValue, errValue)

        self.assertEquals(['handle'], self.observer.calledMethodNames())
        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())

        _, addTimer = self.reactor.calledMethods
        self.assertEquals(((15, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

    def testHandleWithCallableAndData(self):
        suspend = CallTrace('Suspend', returnValues={'__call__': lambda *a, **kw: None})
        handleLog = []
        def handle():
            handleLog.append('ignored-da')
            yield 'ignored-da'
            handleLog.append('Suspend')
            yield suspend
            handleLog.append('ignored-ta')
            yield 'ignored-ta'
            handleLog.append('Stop')
        self.observer.methods['handle'] = handle

        addTimer, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        addProcess, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()

        # 'ignored-da'
        self.assertEquals([], handleLog)
        addProcess.args[0]()
        self.assertEquals(['handle'], self.observer.calledMethodNames())
        handleCall, = self.observer.calledMethods
        self.assertEquals(((), {}), (handleCall.args, handleCall.kwargs))
        self.assertEquals(['ignored-da'], handleLog)
        self.assertEquals([], self.reactor.calledMethodNames())
        self.observer.calledMethods.reset()
        self.reactor.calledMethods.reset()

        # suspend (suspend(reactor, this.next))
        self.assertEquals([], suspend.calledMethodNames())
        addProcess.args[0]()
        self.assertEquals(['ignored-da', 'Suspend'], handleLog)
        self.assertEquals([], self.observer.calledMethodNames())
        self.assertEquals([], self.reactor.calledMethodNames())
        self.assertEquals(['__call__'], suspend.calledMethodNames())
        dunderCall, = suspend.calledMethods
        self.assertEquals(2, len(dunderCall.args))
        self.assertEquals(self.reactor, dunderCall.args[0])
        self.assertEquals(GeneratorType, type(dunderCall.args[1].__self__))
        self.assertEquals('_periodicCall', dunderCall.args[1].__self__.gi_frame.f_code.co_name)
        self.assertEquals({}, dunderCall.kwargs)
        self.observer.calledMethods.reset()
        self.reactor.calledMethods.reset()
        suspend.calledMethods.reset()

        # suspend (suspend.resumeProcess())
        dunderCall.args[1]()
        self.assertEquals(['resumeProcess'], suspend.calledMethodNames())
        resumeProcess, = suspend.calledMethods
        self.assertEquals(((), {}), (resumeProcess.args, resumeProcess.kwargs))
        self.assertEquals([], self.reactor.calledMethodNames())
        self.assertEquals([], self.observer.calledMethodNames())
        self.observer.calledMethods.reset()
        self.reactor.calledMethods.reset()
        suspend.calledMethods.reset()

        # 'ignored-ta'
        addProcess.args[0]()
        self.assertEquals(['ignored-da', 'Suspend', 'ignored-ta'], handleLog)
        self.assertEquals([], suspend.calledMethodNames())
        self.assertEquals([], self.reactor.calledMethodNames())
        self.assertEquals([], self.observer.calledMethodNames())

        # 'Stop'
        addProcess.args[0]()
        self.assertEquals(['ignored-da', 'Suspend', 'ignored-ta', 'Stop'], handleLog)
        self.assertEquals([], suspend.calledMethodNames())
        self.assertEquals([], self.observer.calledMethodNames())
        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        removeProcess, addTimer = self.reactor.calledMethods
        self.assertEquals(((), {}), (removeProcess.args, removeProcess.kwargs))
        self.assertEquals(((3600, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

