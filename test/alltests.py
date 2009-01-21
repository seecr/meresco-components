#!/usr/bin/env python
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

import os, sys
os.system('find .. -name "*.pyc" | xargs rm -f')

import test

from glob import glob
for path in glob('../deps.d/*'):
    sys.path.insert(0, path)

if os.environ.get('PYTHONPATH', '') == '':
    sys.path.insert(0, "..")

import unittest

from sorteditertoolstest import SortedItertoolsTest
from filelisttest import FileListTest
from sortedkeyfiledicttest import SortedKeyFileDictTest
from packertest import PackerTest

from facetindex.lucenedicttest import LuceneDictTest
from facetindex.performancetuningtest import PerformanceTuningTest
from facetindex.docsettest import DocSetTest
from facetindex.docsetlisttest import DocSetListTest
from facetindex.trietest import TrieTest
from facetindex.pooltest import PoolTest
from facetindex.cqlparsetreetolucenequerytest import CqlParseTreeToLuceneQueryTest
from facetindex.cql2lucenequerytest import Cql2LuceneQueryTest

from facetindex.documenttest import DocumentTest
from facetindex.lucenetest import LuceneTest
from facetindex.drilldowntest import DrilldownTest
from facetindex.fields2lucenedocumenttest import Fields2LuceneDocumentTest

from facetindex.incrementalindexingtest import IncrementalIndexingTest

from ngram.ngramtest import NGramTest

# incremental indexing
from facetindex.lucenedocidtrackertest import LuceneDocIdTrackerTest

from oai.fields2oairecordtest import Fields2OaiRecordTest
from oai.oaijazzlucenetest import OaiJazzLuceneTest
from oai.oaigetrecordtest import OaiGetRecordTest
from oai.oailistmetadataformatstest import OaiListMetadataFormatsTest
from oai.oailistsetstest import OaiListSetsTest
from oai.oailisttest import OaiListTest
from oai.oaipmhtest import OaiPmhTest
from oai.oaitooltest import OaiToolTest
from oai.oaiprovenancetest import OaiProvenanceTest
from oai.resumptiontokentest import ResumptionTokenTest
from oai.oaisetselecttest import OaiSetSelectTest
from oai.xml2documenttest import Xml2DocumentTest
from oai.oaijazzfiletest import OaiJazzFileTest
from oai.oaiaddrecordtest import OaiAddRecordTest
from oai.oaijazztest import OaiJazzWithFileTest, OaiJazzWithLuceneTest

if __name__ == '__main__':
    unittest.main()
    os.system('find .. -name "*.pyc" | xargs rm -f')
