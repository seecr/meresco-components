## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from weightless.core import consume, be

from meresco.core import Observable

from meresco.components.onlyadddeleteifchanged import OnlyAddDeleteIfChanged


class OnlyAddDeleteIfChangedTest(SeecrTestCase):
    def setUp(self):
        super(OnlyAddDeleteIfChangedTest, self).setUp()
        self.observer = CallTrace('storageAndMore', emptyGeneratorMethods=['add', 'delete'], returnValues={'getRecord': CallTrace(), 'getData': 'data'})
        self.top = be(
            (Observable(),
                (OnlyAddDeleteIfChanged(),
                    (self.observer,)
                )
            )
        )

    def testAddNew(self):
        self.observer.returnValues['getRecord'] = None
        self.observer.returnValues['getData'] = None
        consume(self.top.all.add(identifier='identifier', partname='partname', data="data"))
        self.assertEqual(['getRecord', 'add'], self.observer.calledMethodNames())
        getRecordCall, addCall = self.observer.calledMethods
        self.assertEqual(dict(identifier='identifier'), getRecordCall.kwargs)
        self.assertEqual(dict(identifier='identifier', partname='partname', data='data'), addCall.kwargs)

    def testAddKnownDataMissing(self):
        self.observer.returnValues['getData'] = None
        consume(self.top.all.add(identifier='identifier', partname='partname', data="data"))
        self.assertEqual(['getRecord', 'getData', 'add'], self.observer.calledMethodNames())
        getRecordCall, getDataCall, addCall = self.observer.calledMethods
        self.assertEqual(dict(identifier='identifier'), getRecordCall.kwargs)
        self.assertEqual(dict(identifier='identifier', name='partname'), getDataCall.kwargs)
        self.assertEqual(dict(identifier='identifier', partname='partname', data='data'), addCall.kwargs)

    def testDeleteNew(self):
        self.observer.returnValues['getRecord'] = None
        consume(self.top.all.delete(identifier='identifier'))
        self.assertEqual(['getRecord', 'delete'], self.observer.calledMethodNames())
        getRecordCall, deleteCall = self.observer.calledMethods
        self.assertEqual(dict(identifier='identifier'), getRecordCall.kwargs)
        self.assertEqual(dict(identifier='identifier'), deleteCall.kwargs)

    def testAddNotChanged(self):
        consume(self.top.all.add(identifier='identifier', partname='partname', data="data"))
        self.assertEqual(['getRecord', 'getData'], self.observer.calledMethodNames())

    def testAddChanged(self):
        observer = CallTrace('storageAndMore', emptyGeneratorMethods=['add'], returnValues={'getRecord': CallTrace(), 'getData': 'data'})
        top = be(
            (Observable(),
                (OnlyAddDeleteIfChanged(),
                    (observer,)
                )
            )
        )
        consume(top.all.add(identifier='identifier', partname='partname', data="different"))
        self.assertEqual(['getRecord', 'getData', 'add'], observer.calledMethodNames())
        getRecordCall, getDataCall, addCall = observer.calledMethods
        self.assertEqual(dict(identifier='identifier'), getRecordCall.kwargs)
        self.assertEqual(dict(identifier='identifier', name='partname'), getDataCall.kwargs)
        self.assertEqual(dict(identifier='identifier', partname='partname', data='different'), addCall.kwargs)

    def testDeleteAlreadAdded(self):
        self.observer.returnValues['getRecord'].isDeleted = False
        consume(self.top.all.delete(identifier='identifier'))
        self.assertEqual(['getRecord', 'delete'], self.observer.calledMethodNames())
        getRecordCall, deleteCall = self.observer.calledMethods
        self.assertEqual(dict(identifier='identifier'), getRecordCall.kwargs)
        self.assertEqual(dict(identifier='identifier'), deleteCall.kwargs)

    def testDeleteAlreadDeleted(self):
        self.observer.returnValues['getRecord'].isDeleted = True
        consume(self.top.all.delete(identifier='identifier'))
        self.assertEqual(['getRecord'], self.observer.calledMethodNames())
