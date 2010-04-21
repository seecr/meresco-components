## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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

from cq2utils import CQ2TestCase, CallTrace
from meresco.components.numeric.numbercomparitorfieldlet import NumberComparitorFieldlet

class NumberComparitorFieldletTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.observer = CallTrace('observer')
        self.fieldsLte = set()
        self.fieldsGte = set()
        def addField(name, value):
            if name.endswith('.gte'):
                self.fieldsGte.add(value)
            if name.endswith('.lte'):
                self.fieldsLte.add(value)
        self.observer.addField = addField

    def testOne(self):
        fieldlet = NumberComparitorFieldlet(nrOfDecimals=1, valueLength=2)
        fieldlet.addObserver(self.observer)
        fieldlet.addField('rating', '2.3')

        self.assertEquals(set(['2z','1z', '0z', 'z3', 'z2','z1', 'z0']), self.fieldsGte)
        self.assertEquals(set(['2z', '3z','4z', '5z', '6z', '7z', '8z', '9z', 'z3','z4','z5','z6','z7','z8','z9']), self.fieldsLte)


    def testFieldlet0_99(self):
        fieldlet = NumberComparitorFieldlet(nrOfDecimals=0, valueLength=5)
        fieldlet.addObserver(self.observer)
        fieldlet.addField('rating', '23')

        self.assertEquals(set(['0zzzz', 'z0zzz', 'zz0zz', 'zzz2z','zzz1z', 'zzz0z', 'zzzz3', 'zzzz2','zzzz1', 'zzzz0']), self.fieldsGte)
        self.assertEquals(['0zzzz','1zzzz', '2zzzz', '3zzzz', '4zzzz', '5zzzz', '6zzzz', '7zzzz', '8zzzz', '9zzzz',\
        'z0zzz', 'z1zzz', 'z2zzz', 'z3zzz', 'z4zzz', 'z5zzz', 'z6zzz', 'z7zzz', 'z8zzz', 'z9zzz',\
        'zz0zz', 'zz1zz', 'zz2zz', 'zz3zz', 'zz4zz', 'zz5zz', 'zz6zz', 'zz7zz', 'zz8zz', 'zz9zz',\
        'zzz2z', 'zzz3z', 'zzz4z', 'zzz5z', 'zzz6z', 'zzz7z', 'zzz8z', 'zzz9z',\
        'zzzz3', 'zzzz4', 'zzzz5', 'zzzz6', 'zzzz7', 'zzzz8', 'zzzz9'], sorted(self.fieldsLte))

    # TODO test met een floor % 10 != 0!!
