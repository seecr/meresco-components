## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
#    Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
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

from meresco.components.msgbox import UpdateAdapterToMsgbox, UpdateAdapterFromMsgbox
from cq2utils import CallTrace, CQ2TestCase
from lxml.etree import parse, tostring
from StringIO import StringIO
from os.path import basename, join

class UpdateAdapterTest(CQ2TestCase):
    def testAddToMsgbox(self):
        adapter = UpdateAdapterToMsgbox()
        msgbox = CallTrace('msgbox')
        adapter.addObserver(msgbox)

        list(adapter.add('identifier', 'partName', 'data'))

        self.assertEquals(1, len(msgbox.calledMethods))
        m = msgbox.calledMethods[0]
        self.assertEquals('add', m.name)
        self.assertEquals((), m.args)
        self.assertEquals({'filename': 'identifier.add', 'filedata': 'data'}, m.kwargs)

    def testDeleteToMsgbox(self):
        adapter = UpdateAdapterToMsgbox()
        msgbox = CallTrace('msgbox')
        adapter.addObserver(msgbox)

        list(adapter.delete('identifier'))

        self.assertEquals(1, len(msgbox.calledMethods))
        m = msgbox.calledMethods[0]
        self.assertEquals('add', m.name)
        self.assertEquals((), m.args)
        self.assertEquals({'filename': 'identifier.delete', 'filedata': ''}, m.kwargs)


    def testAddFromMsgbox(self):
        self._observer = CallTrace("Observer")
        self._updateAdapter = UpdateAdapterFromMsgbox()
        self._updateAdapter.addObserver(self._observer)
        filename = "testFile"
        filepath = join(self.tempdir, filename)
        xml = "<x>testRecord</x>"
        open(filepath, 'w').write(xml)
        file = open(filepath)
        self._updateAdapter.add(filename, file)
        self.assertEquals(1, len(self._observer.calledMethods))
        self.assertEquals("add(identifier='%s', lxmlNode=<etree._ElementTree>)" % basename(filepath), str(self._observer.calledMethods[0]))
        self.assertEquals(xml, tostring(self._observer.calledMethods[0].kwargs['lxmlNode']))

    def testDeleteFromMsgbox(self):
        self._observer = CallTrace("Observer")
        self._updateAdapter = UpdateAdapterFromMsgbox()
        self._updateAdapter.addObserver(self._observer)
        filename = "testFile"
        filepath = join(self.tempdir, filename)
        xml = '<delete id="someId"/>'
        open(filepath, 'w').write(xml)
        file = open(filepath)
        self._updateAdapter.add(filename, file)
        self.assertEquals(1, len(self._observer.calledMethods))
        self.assertEquals("delete(identifier='%s', lxmlNode=<etree._ElementTree>)" % basename(filepath), str(self._observer.calledMethods[0]))
        self.assertEquals(xml, tostring(self._observer.calledMethods[0].kwargs['lxmlNode']))
