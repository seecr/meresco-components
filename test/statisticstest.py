# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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
import cPickle as pickle
from time import time
from random import randint
from seecr.test import SeecrTestCase
from os import makedirs, rename
from os.path import isfile, join
from meresco.components.statistics import Statistics, Logger, combinations, Aggregator, AggregatorException, Top100s, snapshotFilename, log
from meresco.core import Observable
from weightless.core import compose

class StatisticsTest(SeecrTestCase):

    def testStatistics(self):
        stats = Statistics(self.tempdir, [('date',), ('date', 'protocol'), ('date', 'ip', 'protocol')])

        stats._clock = lambda: (1970, 1, 1, 0, 0, 0)
        stats._process({'date':['2007-12-20'], 'ip':['127.0.0.1'], 'protocol':['sru']})
        self.assertEquals({
                ('2007-12-20',): 1
        }, stats.get(('date',), ()))
        self.assertEquals({
                ('2007-12-20', 'sru'): 1,
        }, stats.get(('date', 'protocol')))
        self.assertEquals({
                ('2007-12-20', '127.0.0.1', 'sru'): 1
        }, stats.get(('date', 'ip', 'protocol')))

        stats._process({'date':['2007-12-20'], 'ip':['127.0.0.1'], 'protocol':['srw']})
        self.assertEquals({
                ('2007-12-20',): 2
        }, stats.get(('date',)))
        self.assertEquals({
                ('2007-12-20', 'sru'): 1,
                ('2007-12-20', 'srw'): 1,
        }, stats.get(('date', 'protocol')))
        self.assertEquals({
                ('2007-12-20', '127.0.0.1', 'sru'): 1,
                ('2007-12-20', '127.0.0.1', 'srw'): 1
        }, stats.get(('date', 'ip', 'protocol')))

    def testReadTxLog(self):
        fp = open(self.tempdir + '/txlog', 'w')
        try:
            fp.write("(1970, 1, 1, 0, 0, 0)\t{'date':['2007-12-20'],'ip':['127.0.0.1'],'protocol':['sru']}\n")
            fp.write("(1970, 1, 1, 0, 0, 0)\t{'date':['2007-12-20'],'ip':['127.0.0.1'],'protocol':['srw']}\n")
        finally:
            fp.close()
        stats = Statistics(self.tempdir, [('date',), ('date', 'protocol'), ('date', 'ip', 'protocol')])
        self.assertEquals({
                ('2007-12-20',): 2
        }, stats.get(('date',)))
        self.assertEquals({
                ('2007-12-20', 'sru'): 1,
                ('2007-12-20', 'srw'): 1,
        }, stats.get(('date', 'protocol')))
        self.assertEquals({
                ('2007-12-20', '127.0.0.1', 'sru'): 1,
                ('2007-12-20', '127.0.0.1', 'srw'): 1
        }, stats.get(('date', 'ip', 'protocol')))

    def testWriteTxLog(self):
        def readlines():
            fp = open(self.tempdir + '/txlog')
            try:
                lines = fp.readlines()
            finally:
                fp.close()
            return lines

        stats = Statistics(self.tempdir, [('date',), ('date', 'protocol'), ('date', 'ip', 'protocol')])

        stats._clock = lambda: (1970, 1, 1, 0, 0, 0)
        stats._process({'date':['2007-12-20'], 'ip':['127.0.0.1'], 'protocol':['sru']})

        lines = readlines()
        self.assertEquals(1, len(lines))
        self.assertEquals("(1970, 1, 1, 0, 0, 0)\t{'date': ['2007-12-20'], 'ip': ['127.0.0.1'], 'protocol': ['sru']}\n", lines[0])

        stats._process({'date':['2007-12-20'], 'ip':['127.0.0.1'], 'protocol':['srw']})
        lines = readlines()
        self.assertEquals(2, len(lines))
        self.assertEquals("(1970, 1, 1, 0, 0, 0)\t{'date': ['2007-12-20'], 'ip': ['127.0.0.1'], 'protocol': ['sru']}\n", lines[0])
        self.assertEquals("(1970, 1, 1, 0, 0, 0)\t{'date': ['2007-12-20'], 'ip': ['127.0.0.1'], 'protocol': ['srw']}\n", lines[1])

    def testUndefinedFieldValues(self):
        stats = Statistics(self.tempdir, [('protocol',)])
        stats._process({'date':['2007-12-20']})
        self.assertEquals({}, stats.get(('protocol',)))

        stats = Statistics(self.tempdir, [('date', 'protocol')])
        stats._process({'date':['2007-12-20']})
        self.assertEquals({}, stats.get(('date', 'protocol')))

    def testSnapshotState(self):
        stats = Statistics(self.tempdir, [('keys',)])
        stats._clock = lambda: (1970, 1, 1, 0, 0, 0)
        stats._process({'keys': ['2007-12-20']})
        stats._writeSnapshot()
        self.assertTrue(isfile(join(self.tempdir , snapshotFilename)))
        stats = Statistics(self.tempdir, [('keys',)])
        self.assertEquals({('2007-12-20',): 1}, stats.get(('keys',)))

    def testCrashInWriteSnapshotDuringWriteRecovery(self):
        stats = Statistics(self.tempdir, [('keys',)])
        stats._clock = lambda: (1970, 1, 1, 0, 0, 0)
        stats._process({'keys': ['the old one']})
        stats._writeSnapshot()
        open(self.tempdir + '/txlog', 'w').write("(1970, 1, 1, 0, 0, 0)\t{'keys': ['from_log']}\n")

        snapshotFile = open(join(self.tempdir, snapshotFilename + '.writing'), 'w')
        snapshotFile.write('boom')
        snapshotFile.close()

        stats = Statistics(self.tempdir, [('keys',)])
        self.assertEquals({('the old one',): 1, ('from_log',): 1}, stats.get(('keys',)))

        self.assertFalse(isfile(join(self.tempdir , snapshotFilename + '.writing')))

    def testCrashInWriteSnapshotAfterWriteRecovery(self):
        snapshotFile = open(join(self.tempdir , snapshotFilename), 'wb')
        theOldOne = {'0': Top100s(data={('keys',): {('the old one',): 3}})}
        pickle.dump(theOldOne, snapshotFile)
        snapshotFile.close()

        open(self.tempdir + '/txlog', 'w').write('keys:should_not_appear\n')

        snapshotFile = open(join(self.tempdir, snapshotFilename + '.writing.done'), 'w')
        theNewOne = {'0': Top100s(data={('keys',): {('the new one',): 3}})}
        pickle.dump(theNewOne, snapshotFile)
        snapshotFile.close()

        stats = Statistics(self.tempdir, [('keys',)])
        self.assertEquals(theNewOne, stats._data)
        self.assertFalse(isfile(join(self.tempdir, snapshotFilename + '.writing.done')))
        self.assertTrue(isfile(join(self.tempdir, snapshotFilename)))
        self.assertEquals(theNewOne, pickle.load(open(join(self.tempdir, snapshotFilename))))
        self.assertFalse(isfile(self.tempdir + '/txlog'))
    
    def testRecoverWhenCrashedJustAfterWritingANewSnapshot(self):
        stats = Statistics(self.tempdir, [('keys',)])
        stats._process({'keys': ['the new one']})
        stats._writeSnapshot()
        self.assertEquals({('the new one',):1}, stats.get(('keys',)))
        rename(join(self.tempdir, snapshotFilename), join(self.tempdir, 'new'))
        
        stats = Statistics(self.tempdir, [('keys',)])
        stats._process({'keys': ['the old one']})
        stats._writeSnapshot()
        self.assertEquals({('the old one',):1}, stats.get(('keys',)))
        rename(join(self.tempdir, snapshotFilename), join(self.tempdir, 'old'))
        
        rename(join(self.tempdir, 'old'), join(self.tempdir, snapshotFilename))
        rename(join(self.tempdir, 'new'), join(self.tempdir, snapshotFilename + '.writing.done'))
        open(self.tempdir + '/txlog', 'w').write('keys:should_not_appear\n')

        stats = Statistics(self.tempdir, [('keys',)])
        self.assertFalse(isfile(join(self.tempdir, snapshotFilename + '.writing.done')))
        self.assertTrue(isfile(join(self.tempdir, snapshotFilename)))
        self.assertFalse(isfile(self.tempdir + '/txlog'))
        self.assertEquals({('the new one',):1}, stats.get(('keys',)))

    def testSelfLog(self):
        class MyObserver(Logger):
            def aMessage(self):
                self.log(message='newValue')
        stats = Statistics(self.tempdir, [('message',)])
        stats._clock = lambda: (1970, 1, 1, 0, 0, 0)
        myObserver = MyObserver()
        observable = Observable()
        observable.addObserver(stats)
        stats.addObserver(myObserver)
        list(compose(observable.all.aMessage()))
        self.assertEquals({('newValue',): 1}, stats.get(('message',)))

    def testSelfLogWithObservableAndDelegation(self):
        class MyObserver(Observable):
            log=log
            def aMessage(self):
                self.log(message='newValue')
        stats = Statistics(self.tempdir, [('message',)])
        stats._clock = lambda: (1970, 1, 1, 0, 0, 0)
        myObserver = MyObserver()
        observable = Observable()
        observable.addObserver(stats)
        stats.addObserver(myObserver)
        list(compose(observable.all.aMessage()))
        self.assertEquals({('newValue',): 1}, stats.get(('message',)))

    def testLogWithoutStatistics(self):
        result = []
        class MyObserver(Logger):
            def aMessage(self):
                self.log(message='newValue')
                result.append('aMessage')
        observable = Observable()
        myObserver = MyObserver()
        observable.addObserver(myObserver)
        observable.do.aMessage()
        self.assertEquals(['aMessage'], result)
    
    def testLogWithObserverWithoutStatistics(self):
        result = []
        class MyObserver(Observable):
            log = log
            def aMessage(self):
                self.log(message='newValue')
                result.append('aMessage')
        observable = Observable()
        myObserver = MyObserver()
        observable.addObserver(myObserver)
        observable.do.aMessage()

    def testSelfLogMultipleValuesForSameKey(self):
        class MyObserver(Logger):
            def aMessage(self):
                self.log(message='value1')
                self.log(message='value2')
        stats = Statistics(self.tempdir, [('message',)])
        stats._clock = lambda: (1970, 1, 1, 0, 0, 0)
        myObserver = MyObserver()
        observable = Observable()
        observable.addObserver(stats)
        stats.addObserver(myObserver)
        list(compose(observable.all.aMessage()))
        self.assertEquals({('value1',): 1, ('value2',) : 1}, stats.get(('message',)))

    def testCatchErrorsAndCloseTxLog(self):
        pass

    def testAccumulateOverTime(self):
        stats = Statistics(self.tempdir, [('message',)])
        t0 = (1970, 1, 1, 0, 0, 0)
        stats._clock = lambda: t0
        stats._process({'message': 'A'})
        #count, max, min, avg, pct99
        t1 = (1970, 1, 1, 0, 0, 1)
        stats._process({'message': 'A'})
        self.assertEquals({('A',): 2}, stats.get(('message',), (1970, 1, 1, 0, 0, 0), (1970, 1, 1, 0, 0, 2)))

    def testListKeys(self):
        stats = Statistics(self.tempdir, [('message',), ('ape', 'nut')])
        self.assertEquals([('message',), ('ape', 'nut')], stats.listKeys())

    def testEmptyDataForKey(self):
        stats = Statistics(self.tempdir, [('message',)])
        retval = stats.get(('message',))
        self.assertEquals({}, retval)

    def testObligatoryKey(self):
        stats = Statistics(self.tempdir, [('message',), ('message', 'submessage')])
        stats._clock = lambda: (1970, 1, 1, 0, 0, 0)
        stats._process({'message': 'A', 'submessage': 'B'})
        retval = stats.get(('message',))
        self.assertTrue(retval)

        retval = stats.get(('message', 'submessage'))
        self.assertTrue(retval)

        try:
            stats.get(('not specified',))
            self.fail('must not accept unspecified key')
        except KeyError:
            pass

    def testFlattenValuesNothingToDo(self):
        fieldValues = ([1], [2], [5])
        fieldValuesList = combinations(fieldValues[0], fieldValues[1:])
        self.assertEquals([(1,2,5)], list(fieldValuesList))

    def testFlattenValues(self):
        fieldValues = ([1], [2,3], [4,5])
        fieldValuesList = combinations(fieldValues[0], fieldValues[1:])
        self.assertEquals([(1,2,4),(1,2,5),(1,3,4),(1,3,5)], list(fieldValuesList))

    def testFlattenValues1(self):
        fieldValues = ([1,2], [3,4,5])
        fieldValuesList = combinations(fieldValues[0], fieldValues[1:])
        self.assertEquals([(1,3), (1,4), (1,5), (2,3), (2,4), (2,5)], list(fieldValuesList))

    def testFlattenValues2(self):
        fieldValues = ([1,2], [3,4], [9])
        fieldValuesList = combinations(fieldValues[0], fieldValues[1:])
        self.assertEquals([(1,3,9),(1,4,9),(2,3,9),(2,4,9)], list(fieldValuesList))

    def testSnapshotsTiming(self):
        snapshots = []
        def shuntWriteSnapshot():
            snapshots.append('a snapshot')
            stats._lastSnapshot = stats._clock() #needed because overwritten

        stats = Statistics(self.tempdir, [('date',), ('date', 'protocol'), ('date', 'ip', 'protocol')], snapshotInterval=3600)
        stats._writeSnapshot = shuntWriteSnapshot
        stats._clock = lambda: (1970, 1, 1, 0, 0, 0)
        stats._readState() #must be done again after the clock is shunted

        stats._snapshotIfNeeded()
        self.assertEquals(0, len(snapshots))

        stats._clock = lambda: (1970, 1, 1, 0, 59, 58)
        stats._snapshotIfNeeded()
        self.assertEquals(0, len(snapshots))

        stats._clock = lambda: (1970, 1, 1, 1, 0, 0)
        stats._snapshotIfNeeded()
        self.assertEquals(1, len(snapshots))

        stats._clock = lambda: (1970, 1, 1, 1, 0, 1)
        stats._snapshotIfNeeded()
        self.assertEquals(1, len(snapshots))

    def testStatisticsAggregatorEmpty(self):
        aggregator = Aggregator(ListFactory())
        self.assertEquals([], aggregator.get())

    def testStatisticsAggregatorAddAndGet(self):
        aggregator = Aggregator(ListFactory())

        aggregator._addAt((2000, 1, 1, 0, 0, 0), "value")
        self.assertEquals(["value"], aggregator.get((2000, 1, 1, 0, 0, 0)))
        self.assertEquals(["value"], aggregator.get((2000, 1, 1, 0, 0)))
        self.assertEquals(["value"], aggregator.get((2000, 1, 1, 0)))

    def testStatisticsAggregatorAddTwiceSameTime(self):
        aggregator = Aggregator(ListFactory())
        aggregator._addAt((2000, 1, 1, 0, 0, 0), "value0")
        aggregator._addAt((2000, 1, 1, 0, 0, 0), "value1")
        self.assertEquals(["value0", "value1"], aggregator.get((2000, 1, 1, 0, 0, 0)))

    def testStatisticsAggregatorAddTwiceNewTime(self):
        aggregator = Aggregator(ListFactory())
        aggregator._addAt((2000, 1, 1, 0, 0, 0), "value0")
        aggregator._addAt((2000, 1, 1, 0, 0, 1), "value1")

        self.assertEquals(["value0"], aggregator.get((2000, 1, 1, 0, 0, 0), (2000, 1, 1, 0, 0, 0)))
        self.assertEquals(["value1"], aggregator.get((2000, 1, 1, 0, 0, 1), (2000, 1, 1, 0, 0, 1)))
        self.assertEquals(["value0", "value1"], aggregator.get((2000, 1, 1, 0, 0, 0), (2000, 1, 1, 0, 0, 1)))

    def testStatisticsAggregatorAggregates(self):
        aggregator = Aggregator(ListFactory())
        aggregator._addAt((2000, 1, 1, 0, 0, 0), "value00")
        aggregator._addAt((2000, 1, 1, 0, 0, 1), "value01")
        aggregator._addAt((2000, 1, 1, 0, 1, 0), "should not yet trigger")

        self.assertEquals([], aggregator._root._children[2000]._children[1]._children[1]._children[0]._children[0]._values)
        self.assertEquals(["value00"], aggregator.get((2000, 1, 1, 0, 0, 0), (2000, 1, 1, 0, 0, 0)))

        aggregator._addAt((2000, 1, 1, 0, 2, 0), "trigger")
        self.assertEquals(["value00", "value01"], aggregator._root._children[2000]._children[1]._children[1]._children[0]._children[0]._values)
        try:
            aggregator.get((2000, 1, 1, 0, 0, 0), (2000, 1, 1, 0, 0, 0))
            self.fail()
        except AggregatorException:
            pass
        self.assertEquals(["value00", "value01"], aggregator.get((2000, 1, 1, 0, 0), (2000, 1, 1, 0, 0)))
        self.assertEquals({}, aggregator._root._children[2000]._children[1]._children[1]._children[0]._children[0]._children)

    def testAggregatorRealDataExample(self):
        aggregator = Aggregator(ListFactory())
        aggregator._addAt((2007, 11, 15), "a") # t/m nov zijn geaggregeerd
        aggregator._addAt((2007, 12, 15), "b") # dec heeft alle dagen nog
        aggregator._addAt((2008,  1,  1), "c") # want we zijn nu bij "de derde maand"

        aggregator.get((2007, 12, 15))
        try:
            aggregator.get((2007, 11, 15))
            self.fail("Should raise 'too precise' for 11.15")
        except AggregatorException:
            pass
        result = aggregator.get((2007, 11))
        self.assertEquals(set(["a", "b", "c"]), set(result))

    def testAggregatorPrecisionErrors(self):
        aggregator = Aggregator(ListFactory())
        aggregator._addAt((2000, 0, 0, 0, 0, 0), "a")
        aggregator._addAt((2001, 0, 0, 0, 0, 0), "b")
        aggregator._addAt((2002, 0, 0, 0, 0, 0), "c") #triggers aggregation of 2000
        aggregator._addAt((2003, 3, 3, 3, 3, 3), "d") #triggers aggregation of 2001

        try:
            aggregator.get((2000, 1, 1, 0, 0, 0), (2002, 1, 1, 0, 0, 1))
            self.fail("Should raise 'too precise' for 2000")
        except AggregatorException, e:
            self.assertEquals("fromTime has been accumulated to 'years'.", str(e))

        try:
            aggregator.get((1999, 1, 1, 0, 0, 0), (2001, 1, 1, 0, 0, 1))
            self.fail("Should raise 'too precise' for 2001")
        except AggregatorException, e:
            self.assertEquals("toTime has been accumulated to 'years'.", str(e))

        result = aggregator.get((1999, 1, 1, 0, 0, 0), (2002, 0, 0, 0, 0, 1))
        self.assertEquals(["a", "b", "c"], result)


    def testStatisticsAggregatorAggregatesRecursivelyWithSkippedLevel(self):
        aggregator = Aggregator(ListFactory())
        aggregator._addAt((2000, 1, 1, 0, 0, 0), "value00")
        aggregator._addAt((2000, 1, 1, 0, 0, 1), "value01")
        aggregator._addAt((2000, 1, 1, 1, 0, 0), "should not yet trigger")

        aggregator._addAt((2000, 1, 1, 2, 0, 0), "trigger")
        self.assertEquals(["value00", "value01"], aggregator._root._children[2000]._children[1]._children[1]._children[0]._values)
        try:
            aggregator.get((2000, 1, 1, 0, 0), (2000, 1, 1, 0, 0))
            self.fail()
        except AggregatorException:
            pass
        self.assertEquals(["value00", "value01"], aggregator.get((2000, 1, 1, 0), (2000, 1, 1, 0)))

    def testDataSnapshotStaysCompatible(self):
        data = """eJyVk81u2zAQhO/7IvbJEMUfWcdeCuQSoE3uAk0RrFJHJEQ6cN6+uyvJcZMeKsAQVqRnv50R6VxM
793kA+DDxTGX6eJKnCAJ2LtXP/nsoouTP7j4muLox5IPudgy5DK4DN9CQLFlRQ2u606X4VyGsesg
nl68K5AkPJafScG+Txqedp1dJEMcf1z8xecdJAP7c2rocYSwlfwYew+phTCTREUoISAYCA1kRF6v
1++WbL0jS9T/i3iO2KzKixSV8sZQ3He14nvqq+Ghqnj9zZ5nX8JsZKGkuUGObKSl0HpbLPar2Vst
IJ+I434N537yI+3UvCPhQTAy3PKoOfpar3kEDkBRsUwcljHDB7s2LML3BXkkZFgo7VeK5L9JsYki
uZ2UK0WqO4ok3WcKjyWbbRTOUbYrRVV3FCW+UtS8IzdRFMes9I1i7inNPyg8lmo3UTT31mKlaGz/
tPvt8WCXpCUvKVriI4jnQmvaMPTBcv4YSDc03d8/a/H+abyAeGLmmmat5trg+Jj+XCMeM5prHBqd
zLUES8dyirHQpVafHBtNaGM2OTYNi46rY9Pe5dpUaKxtKFpU0/ra8nSAPzePWl4="""
        from base64 import decodestring
        from zlib import decompress
        snaphotFilename=join(self.tempdir, 'snapshot')
        f = open(snaphotFilename,'w')
        f.write(decompress(decodestring(data)))
        f.close()
        try:
            stats = Statistics(self.tempdir, [('key',)])
            self.fail()
        except ImportError, e:
            self.assertEquals("merescocore.components.statistics has been replaced, therefore you have to convert your statisticsfile using the 'convert_statistics.py' script in the tools directory", str(e))

        #
        # Add the tools package to the python path so the conversion tool can
        # be imported
        # <hack>
        from os.path import dirname, isdir
        toolsPath = join(dirname(dirname(__file__)), 'tools')
        if not isdir(toolsPath):
            return
        from sys import path
        path.insert(0, toolsPath)
        import convert_statistics
        convertedFilename = convert_statistics.convert_pickle_file(snaphotFilename)
        rename(convertedFilename, snaphotFilename)
        # </hack>
        
        stats = Statistics(self.tempdir, [('key',)])
        self.assertEquals({('value',): 1}, stats.get(('key',)))
        
    
    def createStatsdirForMergeTests(self, name):
        statsDir = join(self.tempdir, name)
        makedirs(statsDir)
        stats = Statistics(statsDir, [('protocol',)])
        stats._clock = lambda: (1970, 1, 1, 0, 0, 0)
        stats._process({'protocol':['sru']})
        stats._process({'protocol':['srw']})
        return stats

    def testMergeNode(self):
        stats1 = self.createStatsdirForMergeTests('stats1')
        stats2 = self.createStatsdirForMergeTests('stats2')

        leaf1 = stats1._data._root._children[1970]._children[1]._children[1]._children[0]._children[0]._children[0]
        leaf2 = stats2._data._root._children[1970]._children[1]._children[1]._children[0]._children[0]._children[0]
        self.assertEquals({('protocol',): {('sru',): 1, ('srw',): 1}}, leaf1._values._data)
        self.assertEquals({('protocol',): {('sru',): 1, ('srw',): 1}}, leaf2._values._data)

        leaf1.merge(leaf2)
        self.assertEquals({('protocol',): {('sru',): 2, ('srw',): 2}}, leaf1._values._data)

        self.assertEquals(False, leaf2._aggregated)
        self.assertEquals(False, leaf1._aggregated)

    def testMergeTree(self):
        stats1 = self.createStatsdirForMergeTests('stats1')
        stats2 = self.createStatsdirForMergeTests('stats2')

        root1 = stats1._data._root._children[1970]._children[1]._children[1]._children[0]._children[0]
        root2 = stats2._data._root._children[1970]._children[1]._children[1]._children[0]._children[0]

        self.assertEquals({}, root1._values._data)
        self.assertEquals({}, root2._values._data)

        root1.merge(root2)

        self.assertEquals({('protocol',): {('sru',): 2, ('srw',): 2}}, root1.get(Top100s(), None, None)._data)

        
    def testMergeTreeWherePartsHaveAlreadyBeenAggregated(self):
        stats1 = self.createStatsdirForMergeTests('stats1')
        stats2 = self.createStatsdirForMergeTests('stats2')
        stats1._clock = lambda: (1970, 1, 1, 0, 1, 0)
        stats1._process({'protocol':['srw']})
        stats1._clock = lambda: (1970, 1, 1, 0, 2, 0)
        stats1._process({'protocol':['rss']})

        root1 = stats1._data._root._children[1970]._children[1]._children[1]._children[0]
        root2 = stats2._data._root._children[1970]._children[1]._children[1]._children[0]
        
        self.assertEquals({('protocol',): {('sru',): 1, ('srw',): 2, ('rss',):1}}, root1.get(Top100s(), None, None)._data)
        self.assertEquals({('protocol',): {('sru',): 1, ('srw',): 1}}, root2.get(Top100s(), None, None)._data)

        root1.merge(root2)
        

        self.assertEquals({('protocol',): {('sru',): 2, ('srw',): 3, ('rss',):1}}, root1.get(Top100s(), None, None)._data)

    def testMergeTreeWherePartsHaveAlreadyBeenAggregatedTheOtherWayAround(self):
        stats1 = self.createStatsdirForMergeTests('stats1')
        stats2 = self.createStatsdirForMergeTests('stats2')
        stats1._clock = lambda: (1970, 1, 1, 0, 1, 0)
        stats1._process({'protocol':['srw']})
        stats1._clock = lambda: (1970, 1, 1, 0, 2, 0)
        stats1._process({'protocol':['rss']})

        root1 = stats1._data._root._children[1970]._children[1]._children[1]._children[0]
        root2 = stats2._data._root._children[1970]._children[1]._children[1]._children[0]
        
        self.assertEquals({('protocol',): {('sru',): 1, ('srw',): 2, ('rss',):1}}, root1.get(Top100s(), None, None)._data)
        self.assertEquals({('protocol',): {('sru',): 1, ('srw',): 1}}, root2.get(Top100s(), None, None)._data)
        root2.merge(root1)
        
        self.assertEquals({('protocol',): {('sru',): 2, ('srw',): 3, ('rss',):1}}, root2.get(Top100s(), None, None)._data)

    def testMergeStatistics(self):
        stats1 = self.createStatsdirForMergeTests('stats1')
        stats2 = self.createStatsdirForMergeTests('stats2')
        stats1._clock = lambda: (1970, 1, 1, 0, 1, 0)
        stats1._process({'protocol':['srw']})
        stats1._clock = lambda: (1970, 1, 1, 0, 2, 0)
        stats1._process({'protocol':['rss']})

        self.assertEquals({('sru',): 1, ('srw',): 2, ('rss',):1}, stats1.get(('protocol',)))
        stats1.merge(stats2)
        self.assertEquals({('sru',): 2, ('srw',): 3, ('rss',):1}, stats1.get(('protocol',)))

    def testExtendResults(self):
        one = Top100s({('keys',):dict([('a%02d' % i,10) for i in range(99)] + [('c',5)])})
        two = Top100s({('keys',):dict([('d%02d' % i,8) for i in range(99)] + [('c',6)])})
        one.extend(two)
        self.assertEquals(dict([('a%02d' % i,10) for i in range(99)] + [('c',11)]), one._data[('keys',)])

    def testPerformanceOfSchwartzianTransformInTopSorting(self):
        stats = Statistics(self.tempdir, [('keys',)])
        for i in xrange(1000):
            stats._process({'keys': [randint(0, 10000)]})
        t0 = time()
        for i in xrange(100):
            stats._data.get((2000,1,1,0,0,0), (2099,1,1,0,0,0)).getTop(('keys',))
        t = time() - t0
        self.assertTiming(0.02, t, 0.1) # used to be ~2.5
    
class ListFactory(object):
    def doInit(self):
        return []
    def doAdd(self, values, value):
        values.append(value)
