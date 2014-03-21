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
from weightless.core import be, asString, retval
from meresco.core import Observable, Transparent
from meresco.components.log import LogCollector, collectLog

class LogCollectorTest(SeecrTestCase):

    def testTransparentWontLogIfNothingPresentAll(self):
        observer = createObserver()
        observable = be((Observable(),
            (LogCollector(),
                (observer,)
            )
        ))
        result = asString(observable.all.allMessage('arg', kwarg='kwarg'))
        self.assertEquals('allresult', result)
        result = retval(observable.any.anyMessage('arg', kwarg='kwarg'))
        self.assertEquals('anyresult', result)
        observable.do.doMessage('arg', kwarg='kwarg')
        result = observable.call.callMessage('arg', kwarg='kwarg')
        self.assertEquals('callresult', result)
        self.assertEquals(['allMessage', 'anyMessage', 'doMessage', 'callMessage'], observer.calledMethodNames())
        for m in observer.calledMethods:
            self.assertEquals(('arg',), m.args)
            self.assertEquals(dict(kwarg='kwarg'), m.kwargs)

    def testLog(self):
        class SomeLog(Transparent):
            def logMe(self, argument):
                collectLog(logArgument=argument)
                return self.call.logMe(argument=argument)
        observer = createObserver()
        observer.methods['doNotLogMe'] = observer.methods['logMe'] = observer.methods['callMessage']
        observable = be((Observable(),
            (LogCollector(),
                (SomeLog(),
                    (observer,)
                ),
            )
        ))
        self.assertEquals('callresult', observable.call.logMe(argument=0))
        self.assertEquals('callresult', observable.call.doNotLogMe(argument=0))
        self.assertEquals(['logMe', 'writeLog', 'doNotLogMe'], observer.calledMethodNames())
        writeLog = observer.calledMethods[1]
        self.assertEquals({'logArgument': [0]}, writeLog.kwargs)

    def testCollectLog(self):
        __callstack_var_logCollector__ = LogCollector._logCollector()
        collectLog(key='value1', key2='value2')
        collectLog(key='value3')
        self.assertEquals(dict(key=['value1', 'value3'], key2=['value2']), __callstack_var_logCollector__)

    def testCollectLogWithoutLogCollectorSet(self):
        # AttributeError is a good thing, calling local(...) without result can be expensive!
        self.assertRaises(AttributeError, lambda: collectLog(key='value1', key2='value2'))

def createObserver():
    def allMessage(*args, **kwargs):
        yield 'all'
        yield 'res'
        yield 'ult'
    def anyMessage(*args, **kwargs):
        raise StopIteration('anyresult')
        yield
    return CallTrace('observer', methods={
        'allMessage': allMessage,
        'anyMessage': anyMessage,
        'doMessage': (lambda *args, **kwargs: None),
        'callMessage': (lambda *args, **kwargs: 'callresult')
        })
