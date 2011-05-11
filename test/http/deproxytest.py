# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
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

from cq2utils import CallTrace

from meresco.components.http import Deproxy


class DeproxyTest(TestCase):
    def testClientInCaseNoXForwardedForHeader(self):
        clientfromxforwardedfor = Deproxy()
        observer = CallTrace()
        clientfromxforwardedfor.addObserver(observer)

        observable = Observable()
        observable.addObserver(clientfromxforwardedfor)

        list(observable.any.handleRequest(Client=("1.1.1.1", 11111), Headers={}))

        self.assertEquals(1, len(observer.calledMethods))
        handleRequestCallKwargs = observer.calledMethods[0].kwargs
        self.assertEquals("1.1.1.1", handleRequestCallKwargs['Client'][0])
        self.assertEquals({}, handleRequestCallKwargs['Headers'])


    def testDeproxy(self):
        clientfromxforwardedfor = Deproxy()
        observer = CallTrace()
        clientfromxforwardedfor.addObserver(observer)

        observable = Observable()
        observable.addObserver(clientfromxforwardedfor)

        list(observable.any.handleRequest(
            Client=("1.1.1.1", 11111),
            Headers={"X-Forwarded-For": "2.2.2.2"}))

        self.assertEquals(1, len(observer.calledMethods))
        handleRequestCallKwargs = observer.calledMethods[0].kwargs
        self.assertEquals("2.2.2.2", handleRequestCallKwargs['Client'][0])
        self.assertEquals({"X-Forwarded-For": "2.2.2.2"}, handleRequestCallKwargs['Headers'])

    def testClientFromMulitpleXForwardedForEntries(self):
        clientfromxforwardedfor = Deproxy()
        observer = CallTrace()
        clientfromxforwardedfor.addObserver(observer)

        observable = Observable()
        observable.addObserver(clientfromxforwardedfor)

        list(observable.any.handleRequest(
             Client=("1.1.1.1", 11111),
             Headers={"X-Forwarded-For": "2.2.2.2,3.3.3.3,4.4.4.4"}))

        self.assertEquals(1, len(observer.calledMethods))
        handleRequestCallKwargs = observer.calledMethods[0].kwargs
        self.assertEquals("2.2.2.2", handleRequestCallKwargs['Client'][0])
        self.assertEquals({"X-Forwarded-For": "2.2.2.2,3.3.3.3,4.4.4.4"}, handleRequestCallKwargs['Headers'])

        list(observable.any.handleRequest(
             Client=("1.1.1.1", 11111),
             Headers={"X-Forwarded-For": " 2.2.2.2 , 3.3.3.3,4.4.4.4"}))
        self.assertEquals("2.2.2.2", observer.calledMethods[1].kwargs['Client'][0])

    def testHostFromXForwardedHost(self):
        clientfromxforwardedfor = Deproxy()
        observer = CallTrace()
        clientfromxforwardedfor.addObserver(observer)

        observable = Observable()
        observable.addObserver(clientfromxforwardedfor)

        Headers={
            "Host": "1.1.1.1:11111",
            "X-Forwarded-Host": "2.2.2.2:22222,3.3.3.3:33333,4.4.4.4:44444"
        }
        list(observable.any.handleRequest(Client=("9.9.9.9", 9999), Headers=Headers))

        self.assertEquals(1, len(observer.calledMethods))
        handleRequestCallKwargs = observer.calledMethods[0].kwargs
        self.assertEquals("2.2.2.2:22222", handleRequestCallKwargs['Headers']['Host'])
