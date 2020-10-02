## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2013-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2016 Stichting Kennisnet http://www.kennisnet.nl
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
from meresco.core import Observable
from weightless.core import be, retval, asString
from weightless.io import TimeoutException
from meresco.components import TimedMessageCache, BackoffException
from time import sleep

class TimedMessageCacheTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.init(cacheTimeout=0.1)

    def init(self, **kwargs):
        self.observer = CallTrace('observer')
        self.cache = TimedMessageCache(**kwargs)
        self.dna = be((Observable(),
            (self.cache,
                (self.observer,)
            )
        ))

    def testTransparentForAll(self):
        def someMessage(*args, **kwargs):
            yield 'text'
        self.observer.methods['someMessage'] = someMessage
        result = asString(self.dna.all.someMessage('arg', kwarg='kwarg'))
        self.assertEqual('text', result)
        result = asString(self.dna.all.someMessage('arg', kwarg='kwarg'))
        self.assertEqual('text', result)
        self.assertEqual(['someMessage', 'someMessage'], self.observer.calledMethodNames())

    def testTransparentForDo(self):
        self.observer.methods['someMessage'] = lambda *args, **kwargs: None
        self.dna.do.someMessage('arg', kwarg='kwarg')
        self.dna.do.someMessage('arg', kwarg='kwarg')
        self.assertEqual(['someMessage', 'someMessage'], self.observer.calledMethodNames())

    def testCacheAny(self):
        def someMessage(*args, **kwargs):
            raise StopIteration('result')
            yield
        self.observer.methods['someMessage'] = someMessage
        result = retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual('result', result)
        result = retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual('result', result)
        self.assertEqual(['someMessage'], self.observer.calledMethodNames())
        sleep(0.11)
        result = retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual('result', result)
        self.assertEqual(['someMessage', 'someMessage'], self.observer.calledMethodNames())
        result = retval(self.dna.any.someMessage('arg', kwarg='otherkwarg'))
        self.assertEqual(['someMessage', 'someMessage', 'someMessage'], self.observer.calledMethodNames())

    def testClearCache(self):
        def someMessage(*args, **kwargs):
            raise StopIteration('result')
            yield
        self.observer.methods['someMessage'] = someMessage
        retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual(['someMessage'], self.observer.calledMethodNames())
        self.cache.clear()
        retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual(['someMessage', 'someMessage'], self.observer.calledMethodNames())

    def testKeepValueInCaseOfError(self):
        self.init(cacheTimeout=0.1, returnCachedValueInCaseOfException=True)
        def someMessageResult(*args, **kwargs):
            raise StopIteration('result')
            yield
        def someMessageError(*args, **kwargs):
            raise RuntimeError("could be any exception")
            yield
        self.observer.methods['someMessage'] = someMessageResult
        result = retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual('result', result)
        result = retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual('result', result)
        self.assertEqual(['someMessage'], self.observer.calledMethodNames())
        sleep(0.11)

        self.observer.methods['someMessage'] = someMessageError
        result = retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual('result', result)
        self.assertEqual(['someMessage', 'someMessage'], self.observer.calledMethodNames())

    def testTimeoutExceptionIsRaiseIfNoBackoffTimeoutSet(self):
        self.init(cacheTimeout=0.1)
        def someMessageTimeout(*args, **kwargs):
            raise TimeoutException()
            yield
        self.observer.methods['someMessage'] = someMessageTimeout
        self.assertRaises(TimeoutException, lambda: retval(self.dna.any.someMessage('arg', kwarg='kwarg')))

    def testTimeoutExceptionNotHandledSpecially(self):
        self.init(cacheTimeout=0.1, returnCachedValueInCaseOfException=True)
        def someMessageResult(*args, **kwargs):
            raise StopIteration('result')
            yield
        def someMessageTimeout(*args, **kwargs):
            raise TimeoutException()
            yield
        self.observer.methods['someMessage'] = someMessageResult
        result = retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual(['someMessage'], self.observer.calledMethodNames())
        sleep(0.11)

        self.observer.methods['someMessage'] = someMessageTimeout
        result = retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual('result', result)
        self.assertEqual(['someMessage', 'someMessage'], self.observer.calledMethodNames())

    def testTimeoutExceptionTriggersBackoff(self):
        self.init(cacheTimeout=0.1, returnCachedValueInCaseOfException=True, backoffTimeout=0.1)
        def someMessageResult(*args, **kwargs):
            raise StopIteration('result')
            yield
        def someMessageTimeout(*args, **kwargs):
            raise TimeoutException()
            yield
        self.observer.methods['someMessage'] = someMessageResult
        result = retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual(['someMessage'], self.observer.calledMethodNames())
        sleep(0.11)

        self.observer.methods['someMessage'] = someMessageTimeout
        result = retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual('result', result)
        self.assertEqual(['someMessage', 'someMessage'], self.observer.calledMethodNames())
        result = retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual('result', result)
        # should be in backoff mode and not even try!
        self.assertEqual(['someMessage', 'someMessage'], self.observer.calledMethodNames())
        sleep(0.11)

        self.observer.methods['someMessage'] = someMessageResult
        result = retval(self.dna.any.someMessage('arg', kwarg='kwarg'))
        self.assertEqual('result', result)
        self.assertEqual(['someMessage', 'someMessage', 'someMessage'], self.observer.calledMethodNames())

    def testTimeoutExceptionWithoutCachedResult(self):
        self.init(cacheTimeout=0.1, returnCachedValueInCaseOfException=True, backoffTimeout=0.1)
        def someMessageTimeout(*args, **kwargs):
            raise TimeoutException()
            yield
        self.observer.methods['someMessage'] = someMessageTimeout
        self.assertRaises(BackoffException, lambda: retval(self.dna.any.someMessage('arg', kwarg='kwarg')))
        self.assertEqual(['someMessage'], self.observer.calledMethodNames())
        self.assertRaises(BackoffException, lambda: retval(self.dna.any.someMessage('arg', kwarg='kwarg')))
        self.assertEqual(['someMessage'], self.observer.calledMethodNames())
        sleep(0.11)

        self.assertRaises(BackoffException, lambda: retval(self.dna.any.someMessage('arg', kwarg='kwarg')))
        self.assertEqual(['someMessage', 'someMessage'], self.observer.calledMethodNames())

