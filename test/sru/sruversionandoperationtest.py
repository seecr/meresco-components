## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2017 SURFmarket https://surf.nl
# Copyright (C) 2017-2018, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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
from meresco.components.sru import SruVersionAndOperation
from weightless.core import asString

class SruVersionAndOperationTest(SeecrTestCase):

    def testAutomatic(self):
        def handleRequest(**kwargs):
            yield 'DATA'
        observer = CallTrace(methods=dict(handleRequest=handleRequest))
        vo = SruVersionAndOperation(version='8.7', recordSchema='this')
        vo.addObserver(observer)

        result = asString(vo.handleRequest(arguments={'query':['query'], 'recordSchema': ['schema']}))
        self.assertEqual('DATA', result)
        self.assertEqual(['handleRequest'], observer.calledMethodNames())
        self.assertEqual({
                'arguments': {
                    'query': ['query'],
                    'version': ['8.7'],
                    'operation': ['searchRetrieve'],
                    'recordSchema': ['schema'],
                }
            }, observer.calledMethods[0].kwargs)
        observer.calledMethods.reset()

        result = asString(vo.handleRequest(arguments={'query':['query'], 'version': ['1.2']}))
        self.assertEqual('DATA', result)
        self.assertEqual(['handleRequest'], observer.calledMethodNames())
        self.assertEqual({
                'arguments': {
                    'query': ['query'],
                    'version': ['1.2'],
                    'operation': ['searchRetrieve'],
                    'recordSchema': ['this'],
                }
            }, observer.calledMethods[0].kwargs)
        observer.calledMethods.reset()

        result = asString(vo.handleRequest(arguments={'noquery':['noquery']}))
        self.assertEqual({
                'arguments': {
                    'noquery': ['noquery'],
                }
            }, observer.calledMethods[0].kwargs)
