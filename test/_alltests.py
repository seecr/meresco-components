# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
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

from os import getuid
assert getuid() != 0, "Do not run tests as 'root'"

from os import system                             #DO_NOT_DISTRIBUTE
from sys import path as sysPath                   #DO_NOT_DISTRIBUTE
system('find .. -name "*.pyc" | xargs rm -f')     #DO_NOT_DISTRIBUTE
                                                  #DO_NOT_DISTRIBUTE
from glob import glob                             #DO_NOT_DISTRIBUTE
for path in glob('../deps.d/*'):                  #DO_NOT_DISTRIBUTE
    sysPath.insert(0, path)                       #DO_NOT_DISTRIBUTE
sysPath.insert(0,'..')                            #DO_NOT_DISTRIBUTE

import unittest

from sorteditertoolstest import SortedItertoolsTest
from filelisttest import FileListTest
from berkeleydicttest import DoubleUniqueBerkeleyDictTest, BerkeleyDictTest
from packertest import PackerTest

from facetindex.libfacetindextest import LibFacetIndexTest
from facetindex.docsettest import DocSetTest
from facetindex.docsetlisttest import DocSetListTest
from facetindex.trietest import TrieTest
from facetindex.pooltest import PoolTest
from facetindex.cqlparsetreetolucenequerytest import CqlParseTreeToLuceneQueryTest
from facetindex.cql2lucenequerytest import Cql2LuceneQueryTest
from facetindex.triedicttest import TrieDictTest

from facetindex.documenttest import DocumentTest
from facetindex.lucenetest import LuceneTest
from facetindex.drilldowntest import DrilldownTest
from facetindex.fields2lucenedocumenttest import Fields2LuceneDocumentTest

from facetindex.incrementalindexingtest import IncrementalIndexingTest
from facetindex.integerlisttest import IntegerListTest
from facetindex.clausecollectortest import ClauseCollectorTest

from ngram.ngramtest import NGramTest
from ngram.ngramquerytest import NGramQueryTest
from ngram.ngramindextest import NGramIndexTest
from ngram.cqlsuggestertest import CqlSuggesterTest
from ngram.cqltermvisitortest import CqlTermVisitorTest

# incremental indexing
from facetindex.lucenedocidtrackertest import LuceneDocIdTrackerTest

from oai.fields2oairecordtest import Fields2OaiRecordTest
from oai.oaigetrecordtest import OaiGetRecordTest
from oai.oailistmetadataformatstest import OaiListMetadataFormatsTest
from oai.oailistsetstest import OaiListSetsTest
from oai.oailisttest import OaiListTest
from oai.oaipmhtest import OaiPmhTest, OaiPmhWithIdentifierTest
from oai.oaipmhjazztest import OaiPmhJazzTest
from oai.oaitooltest import OaiToolTest
from oai.oaiprovenancetest import OaiProvenanceTest
from oai.resumptiontokentest import ResumptionTokenTest
from oai.oaisetselecttest import OaiSetSelectTest
from oai.xml2documenttest import Xml2DocumentTest
from oai.oaijazztest import OaiJazzTest
from oai.oaiaddrecordtest import OaiAddRecordTest
from oai.oaijazzimplementationstest import OaiJazzImplementationsTest

from web.webquerytest import WebQueryTest

from inboxtest import InboxTest

if __name__ == '__main__':
    unittest.main()
