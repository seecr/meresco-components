# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from unittest import TestCase

from meresco.core import Observable

from seecr.test import CallTrace

from meresco.components.http import Deproxy

from weightless.core import compose


def handleRequest(*args, **kwargs):
    return
    yield

class DeproxyTest(TestCase):
    def testClientInCaseNoXForwardedForHeader(self):
        clientfromxforwardedfor = Deproxy(deproxyForIps=['1.1.1.1'])
        observer = CallTrace(methods={'handleRequest': handleRequest})
        clientfromxforwardedfor.addObserver(observer)

        observable = Observable()
        observable.addObserver(clientfromxforwardedfor)

        list(compose(observable.all.handleRequest(Client=("1.1.1.1", 11111), Headers={})))

        self.assertEquals(1, len(observer.calledMethods))
        handleRequestCallKwargs = observer.calledMethods[0].kwargs
        self.assertEquals("1.1.1.1", handleRequestCallKwargs['Client'][0])
        self.assertEquals({}, handleRequestCallKwargs['Headers'])


    def testDeproxy(self):
        clientfromxforwardedfor = Deproxy(deproxyForIps=['1.1.1.1'])
        observer = CallTrace(methods={'handleRequest': handleRequest})
        clientfromxforwardedfor.addObserver(observer)

        observable = Observable()
        observable.addObserver(clientfromxforwardedfor)

        list(compose(observable.all.handleRequest(
            Client=("1.1.1.1", 11111),
            Headers={"X-Forwarded-For": "2.2.2.2"})))

        self.assertEquals(1, len(observer.calledMethods))
        handleRequestCallKwargs = observer.calledMethods[0].kwargs
        self.assertEquals("2.2.2.2", handleRequestCallKwargs['Client'][0])
        self.assertEquals({"X-Forwarded-For": "2.2.2.2"}, handleRequestCallKwargs['Headers'])

    def testClientFromMulitpleXForwardedForEntries(self):
        clientfromxforwardedfor = Deproxy(deproxyForIps=['1.1.1.1'])
        observer = CallTrace(methods={'handleRequest': handleRequest})
        clientfromxforwardedfor.addObserver(observer)

        observable = Observable()
        observable.addObserver(clientfromxforwardedfor)

        list(compose(observable.all.handleRequest(
             Client=("1.1.1.1", 11111),
             Headers={"X-Forwarded-For": "2.2.2.2,3.3.3.3,4.4.4.4"})))

        self.assertEquals(1, len(observer.calledMethods))
        handleRequestCallKwargs = observer.calledMethods[0].kwargs
        self.assertEquals("2.2.2.2", handleRequestCallKwargs['Client'][0])
        self.assertEquals({"X-Forwarded-For": "2.2.2.2,3.3.3.3,4.4.4.4"}, handleRequestCallKwargs['Headers'])

        list(compose(observable.all.handleRequest(
             Client=("1.1.1.1", 11111),
             Headers={"X-Forwarded-For": " 2.2.2.2 , 3.3.3.3,4.4.4.4"})))
        self.assertEquals("2.2.2.2", observer.calledMethods[1].kwargs['Client'][0])

    def testHostFromXForwardedHost(self):
        clientfromxforwardedfor = Deproxy(deproxyForIpRanges=[
            ('9.9.9.0', '9.9.9.255')])
        observer = CallTrace(methods={'handleRequest': handleRequest})
        clientfromxforwardedfor.addObserver(observer)

        observable = Observable()
        observable.addObserver(clientfromxforwardedfor)

        Headers={
            "Host": "1.1.1.1:11111",
            "X-Forwarded-Host": "2.2.2.2:22222,3.3.3.3:33333,4.4.4.4:44444"
        }
        list(compose(observable.all.handleRequest(Client=("9.9.9.9", 9999), port='11111', Headers=Headers)))

        self.assertEquals(1, len(observer.calledMethods))
        handleRequestCallKwargs = observer.calledMethods[0].kwargs
        self.assertEquals("2.2.2.2:22222", handleRequestCallKwargs['Headers']['Host'])
        self.assertEquals("22222", handleRequestCallKwargs['port'])

        Headers={
            "Host": "1.1.1.1:11111",
            "X-Forwarded-Host": "2.2.2.2,3.3.3.3:33333,4.4.4.4:44444"
        }
        list(compose(observable.all.handleRequest(Client=("9.9.9.9", 9999), port='11111', Headers=Headers)))

        self.assertEquals(2, len(observer.calledMethods))
        handleRequestCallKwargs = observer.calledMethods[1].kwargs
        self.assertEquals("2.2.2.2", handleRequestCallKwargs['Headers']['Host'])
        self.assertEquals("80", handleRequestCallKwargs['port'])

    def testDeproxyMustHaveIps(self):
        self.assertRaises(ValueError, Deproxy)

    def testDeproxyForIps(self):
        clientfromxforwardedfor = Deproxy(deproxyForIps=['3.3.3.3'])
        observer = CallTrace(methods={'handleRequest': handleRequest})
        clientfromxforwardedfor.addObserver(observer)

        observable = Observable()
        observable.addObserver(clientfromxforwardedfor)

        list(compose(observable.all.handleRequest(
            Client=("1.1.1.1", 11111),
            Headers={"X-Forwarded-For": "2.2.2.2"})))

        self.assertEquals(1, len(observer.calledMethods))
        handleRequestCallKwargs = observer.calledMethods[0].kwargs
        self.assertEquals("1.1.1.1", handleRequestCallKwargs['Client'][0])
        self.assertEquals({"X-Forwarded-For": "2.2.2.2"}, handleRequestCallKwargs['Headers'])

