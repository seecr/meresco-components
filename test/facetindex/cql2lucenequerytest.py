## begin license ##
#
#    Meresco Core is an open-source library containing components to build
#    searchengines, repositories and archives.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Core.
#
#    Meresco Core is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Core; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from unittest import TestCase
from cqlparser import parseString
from merescocomponents.facetindex import CQL2LuceneQuery

class DummyIndex(object):
    def executeQuery(*args, **kwargs):
        pass

class Cql2LuceneQueryTest(TestCase):
    def testLoggingCQL(self):
        convertor = CQL2LuceneQuery({})
        convertor.addObserver(DummyIndex())
        def logShunt(**dict):
            self.dict = dict
        convertor.log = logShunt
        convertor.executeCQL(parseString("term"))
        self.assertEquals({'clause': 'term'}, self.dict)
        convertor.executeCQL(parseString("field=term"))
        self.assertEquals({'clause': 'field = term'}, self.dict)
        convertor.executeCQL(parseString("field =/boost=1.1 term"))
        self.assertEquals({'clause': 'field =/boost=1.1 term'}, self.dict)
        convertor.executeCQL(parseString("field exact term"))
        self.assertEquals({'clause': 'field exact term'}, self.dict)
        convertor.executeCQL(parseString("term1 AND term2"))
        self.assertEquals({'clause': 'term1'}, self.dict)
        convertor.executeCQL(parseString("(term)"))
        self.assertEquals({'clause': 'term'}, self.dict)
        convertor.executeCQL(parseString('field exact "term with spaces"'))
        self.assertEquals({'clause': 'field exact "term with spaces"'}, self.dict)


