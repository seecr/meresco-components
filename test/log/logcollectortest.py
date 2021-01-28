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
from weightless.core import be, asString, retval, consume
from meresco.core import Observable, Transparent
from meresco.components.log import LogCollector, collectLog, LogKeyValue, LogCollectorScope, collectLogForScope
from meresco.components import FilterMessages
from meresco.components.log.utils import getScoped, scopePresent
from seecr.test.io import stderr_replaced

class LogCollectorTest(SeecrTestCase):

    def testTransparentWontLogIfNothingPresentAll(self):
        observer = createObserver()
        observable = be((Observable(),
            (LogCollector(),
                (observer,)
            )
        ))
        result = asString(observable.all.allMessage('arg', kwarg='kwarg'))
        self.assertEqual('allresult', result)
        result = retval(observable.any.anyMessage('arg', kwarg='kwarg'))
        self.assertEqual('anyresult', result)
        observable.do.doMessage('arg', kwarg='kwarg')
        result = observable.call.callMessage('arg', kwarg='kwarg')
        self.assertEqual('callresult', result)
        self.assertEqual(['allMessage', 'anyMessage', 'doMessage', 'callMessage'], observer.calledMethodNames())
        for m in observer.calledMethods:
            self.assertEqual(('arg',), m.args)
            self.assertEqual(dict(kwarg='kwarg'), m.kwargs)

    def testLog(self):
        class SomeLog(Transparent):
            def logMe(self, argument):
                collectLog(dict(logArgument=argument))
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
        self.assertEqual('callresult', observable.call.logMe(argument=0))
        self.assertEqual('callresult', observable.call.doNotLogMe(argument=0))
        self.assertEqual(['logMe', 'writeLog', 'doNotLogMe'], observer.calledMethodNames())
        writeLog = observer.calledMethods[1]
        self.assertEqual((), writeLog.args)
        self.assertEqual(['collectedLog'], list(writeLog.kwargs.keys()))
        self.assertEqual({'logArgument': [0]}, writeLog.kwargs['collectedLog'])

    def testCollectLog(self):
        __callstack_var_logCollector__ = LogCollector._logCollector()
        collectLog(dict(key='value1', key2='value2'))
        collectLog(dict(key='value3'))
        self.assertEqual(dict(key=['value1', 'value3'], key2=['value2']), __callstack_var_logCollector__)

    def testScope(self):
        logwriter = CallTrace('logwriter', emptyGeneratorMethods=['someMessage'])

        top = be((Observable(),
            (LogCollector('default'),
                (logwriter,),
                (FilterMessages(allowed=['someMessage']),
                    (LogKeyValue(dict(name='A')),
                        (LogKeyValue(dict(name='B')),),
                        (LogCollectorScope('scope_one'),
                            (LogKeyValue(dict(name='C')),),
                        ),
                        (LogKeyValue(dict(name='D')),),
                        (LogCollectorScope('scope_two'),
                            (LogKeyValue(dict(name='E')),
                                (LogCollectorScope('scope_two_one'),
                                    (LogKeyValue(dict(name='F')),),
                                ),
                            ),
                            (LogKeyValue(dict(name='G')),),
                        ),
                    )
                )
            )
        ))

        consume(top.all.someMessage())

        self.assertEqual(['someMessage', 'writeLog'], logwriter.calledMethodNames())
        self.assertEqual({
                'name': ['A', 'B', 'D'],
                'scope_one': {
                    'name': ['C'],
                },
                'scope_two': {
                    'name': ['E', 'G'],
                    'scope_two_one': {
                        'name': ['F']
                    }
                }
            }, logwriter.calledMethods[-1].kwargs['collectedLog'])

    def testCollectLogWithoutLogCollectorSet(self):
        # AttributeError is a good thing, calling local(...) without result can be expensive!
        self.assertRaises(AttributeError, lambda: collectLog(dict(key='value1', key2='value2')))

    def testCollectLogForScope(self):
        __callstack_var_logCollector__ = dict()
        collectLogForScope(scope={'key': 'value'})
        collectLogForScope(scope={'key2': 'value'})
        self.assertEqual({'scope': {'key': ['value'], 'key2': ['value']}}, __callstack_var_logCollector__)
        collectLogForScope(scope={'key': 'value2'})
        self.assertEqual({'scope': {'key': ['value', 'value2'], 'key2': ['value']}}, __callstack_var_logCollector__)

    def testGetScoped(self):
        collectedLog = {
            'scope level 1': {
                'scope level 2': {
                    'key': ['value']
                },
                'otherkey': ['other value'],
            },
        }
        self.assertEqual(['value'], getScoped(collectedLog, scopeNames=('scope level 1', 'scope level 2'), key='key'))
        self.assertEqual(['value'], getScoped(collectedLog, scopeNames=('scope level 1', 'scope level 2', 'scope level 3'), key='key'))
        self.assertEqual({}, getScoped(collectedLog, scopeNames=('scope level 1', 'scope level not here', 'scope level 2'), key='key'))
        self.assertEqual(None, getScoped(collectedLog, scopeNames=('scope level 1', 'scope level not here', 'scope level 2'), key='key', default=None))
        self.assertEqual({'key': ['value']}, getScoped(collectedLog, scopeNames=('scope level 1',), key='scope level 2'))
        self.assertEqual({
                'scope level 2': {
                    'key': ['value']
                },
                'otherkey': ['other value'],
            }, getScoped(collectedLog, scopeNames=(), key='scope level 1'))
        self.assertEqual('strange', getScoped(collectedLog, scopeNames=('scope level 1',), key=None, default='strange'))

    def testGetScopeForHttpRequestExample(self):
        collectedLog = {
            'global': {
                'httpRequest': {
                    'path': ['/path']
                },
                'subscope': {
                    'sru': {
                        'numberOfRecords': [0]
                    }
                }
            }
        }
        self.assertEqual({'path': ['/path']}, getScoped(collectedLog, scopeNames=('global', 'subscope'), key='httpRequest'))

    def testScopePresent(self):
        collectedLog = {
            'global': {
                'httpRequest': {
                    'path': ['/path']
                },
                'subscope': {}
            }
        }
        self.assertTrue(scopePresent(collectedLog, scopeNames=('global',)))
        self.assertTrue(scopePresent(collectedLog, scopeNames=('global', 'subscope')))
        self.assertFalse(scopePresent(collectedLog, scopeNames=('global', 'otherscope')))

    def testWriteLogMustNotFail(self):
        logwriter = CallTrace('logwriter', emptyGeneratorMethods=['someMessage'])
        logwriter.exceptions['writeLog'] = ValueError

        top = be((Observable(),
            (LogCollector('default'),
                (logwriter,),
                (FilterMessages(allowed=['someMessage']),
                    (LogKeyValue(dict(name='A')),)
                )
            )
        ))
        with stderr_replaced() as err:
            try:
                consume(top.all.someMessage())
            except ValueError:
                self.fail("Should not raise an error; Only print it")
        self.assertTrue('ValueError' in err.getvalue(), err.getvalue())

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
