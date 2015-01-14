## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
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

from meresco.components.msgbox import UpdateAdapterToMsgbox, UpdateAdapterFromMsgbox, Msgbox
from weightless.core import compose
from seecr.test import SeecrTestCase, CallTrace
from lxml.etree import parse
from meresco.components import lxmltobytes
from io import StringIO
from os.path import basename, join
from os import makedirs

def deleteMock(identifier):
    return
    yield

class UpdateAdapterTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.indir = join(self.tempdir, 'in')
        self.outdir = join(self.tempdir, 'out')
        makedirs(self.indir)
        makedirs(self.outdir)
        self.msgbox = Msgbox('reactor', self.indir, self.outdir)

    def testToAdapterAndMsgboxAdd(self):
        adapter = UpdateAdapterToMsgbox()
        adapter.addObserver(self.msgbox)
        
        list(compose(adapter.add(identifier='identifier', partname='partname', data='data')))
        
        self.assertEqual('data', open(join(self.outdir, 'identifier.add')).read()) 

    def testToAdapterAndMsgboxDelete(self):
        adapter = UpdateAdapterToMsgbox()
        adapter.addObserver(self.msgbox)
        
        list(compose(adapter.delete(identifier='identifier')))
        
        self.assertEqual('', open(join(self.outdir, 'identifier.delete')).read()) 

    def testWrongExtension(self):
        adapter = UpdateAdapterFromMsgbox()
        self.msgbox.addObserver(adapter)
        self.msgbox._logError = lambda *args: None
        open(join(self.indir, 'filename.extension'), 'w').close()

        self.msgbox.processFile('filename.extension')

        errorContents = open(join(self.outdir, 'filename.extension.error')).read()
        self.assertTrue('Expected add or delete as file extension' in errorContents, errorContents)

    def testMsgboxAndFromAdapterDelete(self):
        adapter = UpdateAdapterFromMsgbox()
        observer = CallTrace('observer', methods={'delete': deleteMock})
        self.msgbox.addObserver(adapter)
        adapter.addObserver(observer)
        open(join(self.indir, 'identifier.delete'), 'w').close()

        self.msgbox.processFile('identifier.delete')

        self.assertEqual(['delete'], [m.name for m in observer.calledMethods])
        self.assertEqual({'identifier':'identifier'}, observer.calledMethods[0].kwargs)
        self.assertEqual((), observer.calledMethods[0].args)

    def testMsgboxAndFromAdapterAdd(self):
        adapter = UpdateAdapterFromMsgbox()
        observer = CallTrace('observer')
        addKwargs = {}
        def addMethod(filedata, **kwargs):
            addKwargs['filedata'] = filedata.read()
            addKwargs.update(kwargs)
            return
            yield
        observer.methods['add'] = addMethod
        self.msgbox.addObserver(adapter)
        adapter.addObserver(observer)
        f = open(join(self.indir, 'identifier.add'), 'w')
        f.write('data')
        f.close()

        self.msgbox.processFile('identifier.add')

        self.assertEqual(['add'], [m.name for m in observer.calledMethods])
        self.assertEqual('identifier', addKwargs['identifier'])
        self.assertEqual(None, addKwargs['partname'])
        self.assertEqual('data', addKwargs['filedata'])
        self.assertEqual(3, len(list(addKwargs.items())))

    def testToAdapterAndMsgboxAddEmptyIdentifier(self):
        adapter = UpdateAdapterToMsgbox()
        adapter.addObserver(self.msgbox)
        
        self.assertRaises(ValueError, lambda: list(compose(adapter.add(identifier='', partname='partname', data='data'))))
        self.assertRaises(ValueError, lambda: list(compose(adapter.add(identifier=None, partname='partname', data='data'))))

    def testToAdapterAndMsgboxDeleteEmptyIdentifier(self):
        adapter = UpdateAdapterToMsgbox()
        adapter.addObserver(self.msgbox)
        
        self.assertRaises(ValueError, lambda: list(compose(adapter.delete(identifier=''))))
        self.assertRaises(ValueError, lambda: list(compose(adapter.delete(identifier=None))))

