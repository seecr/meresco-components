## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2013-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from meresco.components import PeriodicCall, Schedule
from meresco.components.periodiccall import shorten, MAX_LENGTH


class PeriodicCallTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.newDNA(schedule=Schedule(period=3600), errorSchedule=Schedule(period=15), prio=9, name='obs_name')
        list(compose(self.dna.once.observer_init()))

    def newDNA(self, **kwargs):
        emptyGeneratorMethods = [kwargs.get('message', 'handle')]
        self.reactor = CallTrace('Reactor', returnValues={'addTimer': 'TOKEN'})
        self.observer = CallTrace('Observer', emptyGeneratorMethods=emptyGeneratorMethods, ignoredAttributes=['observer_init'])
        self.pc = PeriodicCall(self.reactor, **kwargs)
        self.dna = be((Observable(),
            (self.pc,
                (self.observer,),
            ),
        ))

    def testWithoutData(self):
        self.assertEquals('obs_name', self.pc.observable_name())
        self.assertEquals(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods
        self.assertEquals(((3600, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

        # addTimer(3600, pc._periodicCall)
        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        self.assertEquals(['addProcess'], self.reactor.calledMethodNames())
        addProcess, = self.reactor.calledMethods
        self.assertEquals((1, 1), (len(addProcess.args), len(addProcess.kwargs)))
        self.assertEquals({'prio': 9}, addProcess.kwargs)
        thisNext = addProcess.args[0]

        self.reactor.calledMethods.reset()
        self.assertEquals([], self.observer.calledMethodNames())
        thisNext()
        self.assertEquals(['handle'], self.observer.calledMethodNames())
        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        removeProcess, addTimer = self.reactor.calledMethods
        self.assertEquals(((), {}), (removeProcess.args, removeProcess.kwargs))
        self.assertEquals(((3600, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

    def testWithoutDataWithDefaultValues(self):
        self.assertEquals(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods
        self.assertEquals(((3600, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        self.assertEquals(['addProcess'], self.reactor.calledMethodNames())
        addProcess, = self.reactor.calledMethods
        self.assertEquals((1, 1), (len(addProcess.args), len(addProcess.kwargs)))
        self.assertEquals({'prio': 9}, addProcess.kwargs)
        thisNext = addProcess.args[0]

        self.reactor.calledMethods.reset()
        self.assertEquals([], self.observer.calledMethodNames())
        thisNext()
        self.assertEquals(['handle'], self.observer.calledMethodNames())
        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        removeProcess, addTimer = self.reactor.calledMethods
        self.assertEquals(((), {}), (removeProcess.args, removeProcess.kwargs))
        self.assertEquals(((3600, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

    def testAutoStartOrScheduleRequired(self):
        reactor = CallTrace('reactor')

        self.assertRaises(ValueError, lambda: PeriodicCall(reactor=reactor))
        self.assertRaises(ValueError, lambda: PeriodicCall(reactor=reactor, autoStart=True))

        try: PeriodicCall(reactor=reactor, autoStart=False)
        except: self.fail('Unexpected exception')

        try: PeriodicCall(reactor=reactor, schedule=Schedule(period=1), autoStart=False)
        except: self.fail('Unexpected exception')

        try: PeriodicCall(reactor=reactor, schedule=Schedule(period=1), autoStart=True)
        except: self.fail('Unexpected exception')

    def testInitialSchedule(self):
        self.newDNA(initialSchedule=Schedule(period=0), schedule=Schedule(period=12))
        list(compose(self.dna.once.observer_init()))
        self.assertEquals(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods

        self.reactor.calledMethods.reset()
        self.assertEquals(0, addTimer.args[0])
        addTimer.args[1]()

        addProcess, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()
        addProcess.args[0]()

        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        removeProcess, addTimer = self.reactor.calledMethods
        self.assertEquals(12, addTimer.args[0])

    def testSetSchedule(self):
        addTimer, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()
        addTimer.args[1]()

        self.pc.setSchedule(schedule=Schedule(period=1))

        addProcess, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()
        addProcess.args[0]()

        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        removeProcess, addTimer = self.reactor.calledMethods
        self.assertEquals(1, addTimer.args[0])

    def testSetScheduleWithIdenticalScheduleDoesNothing(self):
        addTimer, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()
        self.assertEquals(3600, addTimer.args[0])
        self.pc.setSchedule(schedule=Schedule(period=3600))
        self.assertEquals([], self.reactor.calledMethodNames())

    def testSetScheduleAddsANewTimer(self):
        self.reactor.calledMethods.reset()
        self.pc.setSchedule(schedule=Schedule(period=123))
        self.assertEquals(['removeTimer', 'addTimer'], self.reactor.calledMethodNames())
        removeTimer, addTimer = self.reactor.calledMethods
        self.assertEquals('TOKEN', removeTimer.args[0])
        self.assertEquals(123, addTimer.args[0])

    def testErrorIntervalAndLoggedMessage(self):
        def raiser():
            raise Exception('exception')
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
            self.assertTrue(errValue.startswith(repr(self.pc)))
            self.assertTrue('Traceback' in errValue, errValue)
            self.assertTrue('Exception: exception' in errValue, errValue)
            self.assertEquals('exception', self.pc.getState().errorState)

        self.assertEquals(['handle'], self.observer.calledMethodNames())
        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())

        _, addTimer = self.reactor.calledMethods
        self.assertEquals(((15, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

    def testFatalErrorReRaised(self):
        for exception in [KeyboardInterrupt, SystemExit, AssertionError]:
            self.newDNA(schedule=Schedule(period=987))
            def raiser():
                raise exception('msg')
                yield
            self.observer.methods['handle'] = raiser
            list(compose(self.dna.once.observer_init()))

            addTimer, = self.reactor.calledMethods
            self.reactor.calledMethods.reset()
            addTimer.args[1]()
            addProcess, = self.reactor.calledMethods
            self.reactor.calledMethods.reset()

            try:
                addProcess.args[0]()
            except exception:
                pass
            else:
                self.fail()

            self.assertEquals(['handle'], self.observer.calledMethodNames())
            self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())

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

    @stderr_replaced
    def testPausePausesOnStart(self):
        # autoStart
        reactor = CallTrace('reactor')
        pc = PeriodicCall(reactor=reactor, autoStart=False)
        pc.observer_init()
        self.assertEquals([], reactor.calledMethodNames())

        # explicit .pause()
        pc = PeriodicCall(reactor=reactor, schedule=Schedule(period=1), autoStart=True)
        pc.pause()
        pc.observer_init()
        self.assertEquals([], reactor.calledMethodNames())

    @stderr_replaced
    def testPausePausesWhenRunning(self):
        self.newDNA(schedule=Schedule(period=1), autoStart=True)
        list(compose(self.dna.once.observer_init()))
        self.assertEquals(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods

        # pauses after completing current task
        self.pc.pause()

        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        self.assertEquals(['addProcess'], self.reactor.calledMethodNames())
        addProcess, = self.reactor.calledMethods

        self.reactor.calledMethods.reset()
        addProcess.args[0]()
        self.assertEquals(['handle'], self.observer.calledMethodNames())
        self.assertEquals(['removeProcess'], self.reactor.calledMethodNames())

    def testPauseRemovesInitialPendingTimer(self):
        self.assertEquals(['addTimer'], self.reactor.calledMethodNames())

        self.reactor.calledMethods.reset()
        with stderr_replaced() as err:
            self.pc.pause()
            self.assertEquals('%s: paused\n' % repr(self.pc), err.getvalue())
        self.assertEquals(['removeTimer'], self.reactor.calledMethodNames())
        removeTimer, = self.reactor.calledMethods
        self.assertEquals((('TOKEN',), {}), (removeTimer.args, removeTimer.kwargs))

    def testPauseRemovesEndOfProcessPendingTimer(self):
        self.assertEquals(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()

        # Process until timer added again
        addTimer.args[1]()
        addProcess, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()
        addProcess.args[0]()
        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        self.reactor.calledMethods.reset()

        # pause at pending timer
        with stderr_replaced() as err:
            self.pc.pause()
            self.assertEquals('%s: paused\n' % repr(self.pc), err.getvalue())
        self.assertEquals(['removeTimer'], self.reactor.calledMethodNames())
        removeTimer, = self.reactor.calledMethods
        self.assertEquals((('TOKEN',), {}), (removeTimer.args, removeTimer.kwargs))

    def testResumeStartsWhenPaused(self):
        self.newDNA(schedule=Schedule(period=2), autoStart=False)
        list(compose(self.dna.once.observer_init()))
        self.assertEquals([], self.reactor.calledMethodNames())

        with stderr_replaced() as err:
            self.pc.resume()
            self.assertEquals('%s: resumed\n' % repr(self.pc), err.getvalue())
        self.assertEquals(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods
        self.assertEquals(self.pc._periodicCall, addTimer.args[1])

        # finish one task (1/2)
        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        addProcess, = self.reactor.calledMethods

        # finish one task (2/2)
        self.reactor.calledMethods.reset()
        addProcess.args[0]()
        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())

    @stderr_replaced
    def testDoNotResumeNotPaused(self):
        self.newDNA(schedule=Schedule(period=1), autoStart=True)
        self.pc.resume()
        self.assertEquals([], self.reactor.calledMethodNames())

        list(compose(self.dna.once.observer_init()))
        self.assertEquals(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods

        self.reactor.calledMethods.reset()
        self.pc.resume()
        self.assertEquals([], self.reactor.calledMethodNames())

        addTimer.args[1]()
        self.assertEquals(['addProcess'], self.reactor.calledMethodNames())

        self.reactor.calledMethods.reset()
        self.pc.resume()
        self.assertEquals([], self.reactor.calledMethodNames())

    @stderr_replaced
    def testResumeOnlyAddsATimerWhenNotBusy(self):
        # Because at the end of the busy / reactor processing it
        # will add a timer when not paused.
        addTimer, = self.reactor.calledMethods

        # "Firing" timer callback
        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        self.assertEquals(['addProcess'], self.reactor.calledMethodNames())
        addProcess, = self.reactor.calledMethods
        busybusy = []
        def handleBusyMock():
            yield  busybusy.append(True)
            yield  busybusy.append(True)
        self.observer.methods['handle'] = handleBusyMock

        # Busy processing, so pause won't work immediately
        self.reactor.calledMethods.reset()
        self.pc.pause()  # <-- pause
        self.assertEquals([], self.reactor.calledMethodNames())
        self.assertEquals([], busybusy)
        addProcess.args[0]()  # <-- doing stuff
        self.assertEquals([], self.reactor.calledMethodNames())
        self.assertEquals([True], busybusy)
        self.pc.resume()  # <-- resume called

        addProcess.args[0]()  # <-- doing more stuff
        self.assertEquals([True, True], busybusy)
        self.assertEquals([], self.reactor.calledMethodNames())
        addProcess.args[0]()  # <-- done doing and delayed resume (addTimer)
        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())

    @stderr_replaced
    def testGetState(self):
        state = self.pc.getState()
        self.assertEquals('obs_name', state.name)
        self.assertEquals(False, state.paused)
        self.assertEquals(Schedule(period=3600), state.schedule)
        self.assertEquals({'paused': False, 'name': 'obs_name', 'schedule': Schedule(period=3600)}, state.asDict())

        self.pc.observable_setName('dashy')
        self.assertEquals('dashy', state.name)
        self.assertEquals(None, state.errorState)

        self.pc.setSchedule(schedule=Schedule(period=5))
        self.assertEquals(Schedule(period=5), state.schedule)

        self.pc.pause()
        self.assertEquals(True, state.paused)

        self.pc.resume()
        addTimer = self.reactor.calledMethods[-1]
        self.reactor.calledMethods.reset()
        self.assertEquals(False, state.paused)

        addTimer.args[1]()
        self.pc.pause()
        self.assertEquals(False, state.paused)

        addProcess = self.reactor.calledMethods[-1]
        addProcess.args[0]()
        self.assertEquals(True, state.paused)

    def testRepr(self):
        self.assertEquals("PeriodicCall(name='obs_name', paused=False, schedule=Schedule(period=3600))", repr(self.pc))

    def testShorten(self):
        message = 'x' * (MAX_LENGTH)
        self.assertEquals(message, message)

        message = 'x' * (MAX_LENGTH) + 'z'
        self.assertNotEqual(message, shorten(message))
        self.assertEquals(MAX_LENGTH + len(' ... '), len(shorten(message)))
        self.assertTrue(' ... ' in shorten(message), shorten(message))
        self.assertTrue(shorten(message).startswith('xxxx'), shorten(message))
        self.assertTrue(shorten(message).endswith('xxxz'), shorten(message))

    def testMessageConfigurable(self):
        self.newDNA(message="aMessage", schedule=Schedule(period=3600), errorSchedule=Schedule(period=15), prio=9, name='obs_name')
        list(compose(self.dna.once.observer_init()))

        self.assertEquals(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods
        callback = addTimer.args[1]
        self.reactor.calledMethods.reset()
        callback()
        self.assertEquals(['addProcess'], self.reactor.calledMethodNames())
        addProcess, = self.reactor.calledMethods
        callback = addProcess.args[0]
        self.reactor.calledMethods.reset()
        callback()
        self.assertEquals(['aMessage'], self.observer.calledMethodNames())
