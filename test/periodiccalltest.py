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

from weightless.core import be, compose, Yield

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
        self.assertEqual('obs_name', self.pc.observable_name())
        self.assertEqual(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods
        self.assertEqual(((3600, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

        # addTimer(3600, pc._periodicCall)
        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        self.assertEqual(['addProcess'], self.reactor.calledMethodNames())
        addProcess, = self.reactor.calledMethods
        self.assertEqual((1, 1), (len(addProcess.args), len(addProcess.kwargs)))
        self.assertEqual({'prio': 9}, addProcess.kwargs)
        thisNext = addProcess.args[0]

        self.reactor.calledMethods.reset()
        self.assertEqual([], self.observer.calledMethodNames())
        thisNext()
        self.assertEqual(['handle'], self.observer.calledMethodNames())
        self.assertEqual(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        removeProcess, addTimer = self.reactor.calledMethods
        self.assertEqual(((), {}), (removeProcess.args, removeProcess.kwargs))
        self.assertEqual(((3600, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

    def testWithoutDataWithDefaultValues(self):
        self.assertEqual(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods
        self.assertEqual(((3600, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        self.assertEqual(['addProcess'], self.reactor.calledMethodNames())
        addProcess, = self.reactor.calledMethods
        self.assertEqual((1, 1), (len(addProcess.args), len(addProcess.kwargs)))
        self.assertEqual({'prio': 9}, addProcess.kwargs)
        thisNext = addProcess.args[0]

        self.reactor.calledMethods.reset()
        self.assertEqual([], self.observer.calledMethodNames())
        thisNext()
        self.assertEqual(['handle'], self.observer.calledMethodNames())
        self.assertEqual(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        removeProcess, addTimer = self.reactor.calledMethods
        self.assertEqual(((), {}), (removeProcess.args, removeProcess.kwargs))
        self.assertEqual(((3600, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

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
        self.assertEqual(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods

        self.reactor.calledMethods.reset()
        self.assertEqual(0, addTimer.args[0])
        addTimer.args[1]()

        addProcess, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()
        addProcess.args[0]()

        self.assertEqual(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        removeProcess, addTimer = self.reactor.calledMethods
        self.assertEqual(12, addTimer.args[0])

    def testSetSchedule(self):
        addTimer, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()
        addTimer.args[1]()

        self.pc.setSchedule(schedule=Schedule(period=1))

        addProcess, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()
        addProcess.args[0]()

        self.assertEqual(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        removeProcess, addTimer = self.reactor.calledMethods
        self.assertEqual(1, addTimer.args[0])

    def testSetScheduleWithIdenticalScheduleDoesNothing(self):
        addTimer, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()
        self.assertEqual(3600, addTimer.args[0])
        self.pc.setSchedule(schedule=Schedule(period=3600))
        self.assertEqual([], self.reactor.calledMethodNames())

    def testSetScheduleAddsANewTimer(self):
        self.reactor.calledMethods.reset()
        self.pc.setSchedule(schedule=Schedule(period=123))
        self.assertEqual(['removeTimer', 'addTimer'], self.reactor.calledMethodNames())
        removeTimer, addTimer = self.reactor.calledMethods
        self.assertEqual('TOKEN', removeTimer.args[0])
        self.assertEqual(123, addTimer.args[0])

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
            self.assertEqual('exception', self.pc.getState().errorState)

        self.assertEqual(['handle'], self.observer.calledMethodNames())
        self.assertEqual(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())

        _, addTimer = self.reactor.calledMethods
        self.assertEqual(((15, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

    def testErrorStateReset(self):
        handleCalledBefore = []
        def handle():
            if not handleCalledBefore:
                handleCalledBefore.append(True)
                raise Exception('exception')
            yield Yield
        self.observer.methods['handle'] = handle

        addTimer, = self.reactor.calledMethods
        timerCallback = addTimer.args[1]
        self.reactor.calledMethods.reset()
        timerCallback()
        addProcess, = self.reactor.calledMethods
        addProcessCallback = addProcess.args[0]
        self.reactor.calledMethods.reset()

        with stderr_replaced():
            addProcessCallback()
            self.assertEquals('exception', self.pc.getState().errorState)

        self.assertEquals(['handle'], self.observer.calledMethodNames())
        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())

        _, addTimer = self.reactor.calledMethods
        timerCallback = addTimer.args[1]
        self.reactor.calledMethods.reset()
        timerCallback()
        addProcess, = self.reactor.calledMethods
        addProcessCallback = addProcess.args[0]
        self.reactor.calledMethods.reset()
        addProcessCallback()
        self.assertEquals(['handle', 'handle'], self.observer.calledMethodNames())
        addProcessCallback()
        self.assertEquals(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        self.assertEquals(None, self.pc.getState().errorState)

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

            self.assertEqual(['handle'], self.observer.calledMethodNames())
            self.assertEqual(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())

    def testHandleWithCallableAndData(self):
        suspend = CallTrace('Suspend', returnValues={'__call__': None})
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
        self.assertEqual([], handleLog)
        addProcess.args[0]()
        self.assertEqual(['handle'], self.observer.calledMethodNames())
        handleCall, = self.observer.calledMethods
        self.assertEqual(((), {}), (handleCall.args, handleCall.kwargs))
        self.assertEqual(['ignored-da'], handleLog)
        self.assertEqual([], self.reactor.calledMethodNames())
        self.observer.calledMethods.reset()
        self.reactor.calledMethods.reset()

        # suspend (suspend(reactor, this.next))
        self.assertEqual([], suspend.calledMethodNames())
        addProcess.args[0]()
        self.assertEqual(['ignored-da', 'Suspend'], handleLog)
        self.assertEqual([], self.observer.calledMethodNames())
        self.assertEqual([], self.reactor.calledMethodNames())
        self.assertEqual(['__call__'], suspend.calledMethodNames())
        dunderCall, = suspend.calledMethods
        self.assertEqual(2, len(dunderCall.args))
        self.assertEqual(self.reactor, dunderCall.args[0])
        self.assertEqual(GeneratorType, type(dunderCall.args[1].__self__))
        self.assertEqual('_periodicCall', dunderCall.args[1].__self__.gi_frame.f_code.co_name)
        self.assertEqual({}, dunderCall.kwargs)
        self.assertEqual(2, len(dunderCall.args))
        self.assertEqual(self.reactor, dunderCall.args[0])
        self.assertEqual(GeneratorType, type(dunderCall.args[1].__self__))
        self.assertEqual('_periodicCall', dunderCall.args[1].__self__.gi_frame.f_code.co_name)
        self.assertEqual({}, dunderCall.kwargs)
        self.observer.calledMethods.reset()
        self.reactor.calledMethods.reset()
        suspend.calledMethods.reset()

        # suspend (suspend.resumeProcess())
        dunderCall.args[1]()
        self.assertEqual(['resumeProcess'], suspend.calledMethodNames())
        resumeProcess, = suspend.calledMethods
        self.assertEqual(((), {}), (resumeProcess.args, resumeProcess.kwargs))
        self.assertEqual([], self.reactor.calledMethodNames())
        self.assertEqual([], self.observer.calledMethodNames())
        self.observer.calledMethods.reset()
        self.reactor.calledMethods.reset()
        suspend.calledMethods.reset()

        # 'ignored-ta'
        addProcess.args[0]()
        self.assertEqual(['ignored-da', 'Suspend', 'ignored-ta'], handleLog)
        self.assertEqual([], suspend.calledMethodNames())
        self.assertEqual([], self.reactor.calledMethodNames())
        self.assertEqual([], self.observer.calledMethodNames())

        # 'Stop'
        addProcess.args[0]()
        self.assertEqual(['ignored-da', 'Suspend', 'ignored-ta', 'Stop'], handleLog)
        self.assertEqual([], suspend.calledMethodNames())
        self.assertEqual([], self.observer.calledMethodNames())
        self.assertEqual(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        removeProcess, addTimer = self.reactor.calledMethods
        self.assertEqual(((), {}), (removeProcess.args, removeProcess.kwargs))
        self.assertEqual(((3600, self.pc._periodicCall), {}), (addTimer.args, addTimer.kwargs))

    @stderr_replaced
    def testPausePausesOnStart(self):
        # autoStart
        reactor = CallTrace('reactor')
        pc = PeriodicCall(reactor=reactor, autoStart=False)
        pc.observer_init()
        self.assertEqual([], reactor.calledMethodNames())

        # explicit .pause()
        pc = PeriodicCall(reactor=reactor, schedule=Schedule(period=1), autoStart=True)
        pc.pause()
        pc.observer_init()
        self.assertEqual([], reactor.calledMethodNames())

    @stderr_replaced
    def testPausePausesWhenRunning(self):
        self.newDNA(schedule=Schedule(period=1), autoStart=True)
        list(compose(self.dna.once.observer_init()))
        self.assertEqual(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods

        # pauses after completing current task
        self.pc.pause()

        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        self.assertEqual(['addProcess'], self.reactor.calledMethodNames())
        addProcess, = self.reactor.calledMethods

        self.reactor.calledMethods.reset()
        addProcess.args[0]()
        self.assertEqual(['handle'], self.observer.calledMethodNames())
        self.assertEqual(['removeProcess'], self.reactor.calledMethodNames())

    def testPauseRemovesInitialPendingTimer(self):
        self.assertEqual(['addTimer'], self.reactor.calledMethodNames())

        self.reactor.calledMethods.reset()
        with stderr_replaced() as err:
            self.pc.pause()
            self.assertEqual('%s: paused\n' % repr(self.pc), err.getvalue())
        self.assertEqual(['removeTimer'], self.reactor.calledMethodNames())
        removeTimer, = self.reactor.calledMethods
        self.assertEqual((('TOKEN',), {}), (removeTimer.args, removeTimer.kwargs))

    def testPauseRemovesEndOfProcessPendingTimer(self):
        self.assertEqual(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()

        # Process until timer added again
        addTimer.args[1]()
        addProcess, = self.reactor.calledMethods
        self.reactor.calledMethods.reset()
        addProcess.args[0]()
        self.assertEqual(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())
        self.reactor.calledMethods.reset()

        # pause at pending timer
        with stderr_replaced() as err:
            self.pc.pause()
            self.assertEqual('%s: paused\n' % repr(self.pc), err.getvalue())
        self.assertEqual(['removeTimer'], self.reactor.calledMethodNames())
        removeTimer, = self.reactor.calledMethods
        self.assertEqual((('TOKEN',), {}), (removeTimer.args, removeTimer.kwargs))

    def testResumeStartsWhenPaused(self):
        self.newDNA(schedule=Schedule(period=2), autoStart=False)
        list(compose(self.dna.once.observer_init()))
        self.assertEqual([], self.reactor.calledMethodNames())

        with stderr_replaced() as err:
            self.pc.resume()
            self.assertEqual('%s: resumed\n' % repr(self.pc), err.getvalue())
        self.assertEqual(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods
        self.assertEqual(self.pc._periodicCall, addTimer.args[1])

        # finish one task (1/2)
        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        addProcess, = self.reactor.calledMethods

        # finish one task (2/2)
        self.reactor.calledMethods.reset()
        addProcess.args[0]()
        self.assertEqual(['removeProcess', 'addTimer'], self.reactor.calledMethodNames())

    @stderr_replaced
    def testDoNotResumeNotPaused(self):
        self.newDNA(schedule=Schedule(period=1), autoStart=True)
        self.pc.resume()
        self.assertEqual([], self.reactor.calledMethodNames())

        list(compose(self.dna.once.observer_init()))
        self.assertEqual(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods

        self.reactor.calledMethods.reset()
        self.pc.resume()
        self.assertEqual([], self.reactor.calledMethodNames())

        addTimer.args[1]()
        self.assertEqual(['addProcess'], self.reactor.calledMethodNames())

        self.reactor.calledMethods.reset()
        self.pc.resume()
        self.assertEqual([], self.reactor.calledMethodNames())

    @stderr_replaced
    def testResumeOnlyAddsATimerWhenNotBusy(self):
        # Because at the end of the busy / reactor processing it
        # will add a timer when not paused.
        addTimer, = self.reactor.calledMethods

        # "Firing" timer callback
        self.reactor.calledMethods.reset()
        addTimer.args[1]()
        self.assertEqual(['addProcess'], self.reactor.calledMethodNames())
        addProcess, = self.reactor.calledMethods
        busybusy = []
        def handleBusyMock():
            yield  busybusy.append(True)
            yield  busybusy.append(True)
        self.observer.methods['handle'] = handleBusyMock

        # Busy processing, so pause won't work immediately
        self.reactor.calledMethods.reset()
        self.pc.pause()  # <-- pause
        self.assertEqual([], self.reactor.calledMethodNames())
        self.assertEqual([], busybusy)
        addProcess.args[0]()  # <-- doing stuff
        self.assertEqual([], self.reactor.calledMethodNames())
        self.assertEqual([True], busybusy)
        self.pc.resume()  # <-- resume called

        addProcess.args[0]()  # <-- doing more stuff
        self.assertEqual([True, True], busybusy)

    @stderr_replaced
    def testGetState(self):
        state = self.pc.getState()
        self.assertEqual('obs_name', state.name)
        self.assertEqual(False, state.paused)
        self.assertEqual(Schedule(period=3600), state.schedule)
        self.assertEqual({'paused': False, 'name': 'obs_name', 'schedule': Schedule(period=3600)}, state.asDict())

        self.pc.observable_setName('dashy')
        self.assertEqual('dashy', state.name)
        self.assertEqual(None, state.errorState)

        self.pc.setSchedule(schedule=Schedule(period=5))
        self.assertEqual(Schedule(period=5), state.schedule)

        self.pc.pause()
        self.assertEqual(True, state.paused)

        self.pc.resume()
        addTimer = self.reactor.calledMethods[-1]
        self.reactor.calledMethods.reset()
        self.assertEqual(False, state.paused)

        addTimer.args[1]()
        self.pc.pause()
        self.assertEqual(False, state.paused)

        addProcess = self.reactor.calledMethods[-1]
        addProcess.args[0]()
        self.assertEqual(True, state.paused)

    def testRepr(self):
        self.assertEqual("PeriodicCall(name='obs_name', paused=False, schedule=Schedule(period=3600))", repr(self.pc))

    def testShorten(self):
        message = 'x' * (MAX_LENGTH)
        self.assertEqual(message, message)

        message = 'x' * (MAX_LENGTH) + 'z'
        self.assertNotEqual(message, shorten(message))
        self.assertEqual(MAX_LENGTH + len(' ... '), len(shorten(message)))
        self.assertTrue(' ... ' in shorten(message), shorten(message))
        self.assertTrue(shorten(message).startswith('xxxx'), shorten(message))
        self.assertTrue(shorten(message).endswith('xxxz'), shorten(message))

    def testMessageConfigurable(self):
        self.newDNA(message="aMessage", schedule=Schedule(period=3600), errorSchedule=Schedule(period=15), prio=9, name='obs_name')
        list(compose(self.dna.once.observer_init()))

        self.assertEqual(['addTimer'], self.reactor.calledMethodNames())
        addTimer, = self.reactor.calledMethods
        callback = addTimer.args[1]
        self.reactor.calledMethods.reset()
        callback()
        self.assertEqual(['addProcess'], self.reactor.calledMethodNames())
        addProcess, = self.reactor.calledMethods
        callback = addProcess.args[0]
        self.reactor.calledMethods.reset()
        callback()
        self.assertEqual(['aMessage'], self.observer.calledMethodNames())
