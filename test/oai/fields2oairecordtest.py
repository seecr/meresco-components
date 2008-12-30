## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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

from cq2utils import CQ2TestCase, CallTrace

from merescocomponents.oai import Fields2OaiRecordTx

class Fields2OaiRecordTest(CQ2TestCase):
    def testOne(self):
        transaction = CallTrace('Transaction')
        rm = CallTrace('ResourceManager')
        rm.tx = transaction
        rm.do = rm
        transaction.locals = {'id':'identifier'}
        
        tx = Fields2OaiRecordTx(rm)
        
        tx.addField('set', ('setSpec', 'setName'))
        tx.addField('metadataFormat', ('prefix', 'schema', 'namespace'))
        tx.commit()

        self.assertEquals(1, len(rm.calledMethods))
        self.assertEquals('addOaiRecord', rm.calledMethods[0].name)
        self.assertEquals({'identifier':'identifier',
                'metadataFormats': set([('prefix', 'schema', 'namespace')]),
                'sets': set([('setSpec', 'setName')])},
            rm.calledMethods[0].kwargs)

    def testNothing(self):
        transaction = CallTrace('Transaction')
        rm = CallTrace('ResourceManager')
        rm.tx = transaction
        rm.do = rm
        transaction.locals = {'id':'identifier'}
        
        tx = Fields2OaiRecordTx(rm)
        
        tx.addField('set', ('setSpec', 'setName'))
        tx.commit()

        self.assertEquals(0, len(rm.calledMethods))
        
