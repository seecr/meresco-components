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
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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

from berkeleydicttest import DoubleUniqueBerkeleyDictTest, BerkeleyDictTest
from contextsettest import ContextSetTest
from cqlconversiontest import CQLConversionTest
from fieldletstest import FieldletsTest
from fields2xmltest import Fields2XmlTest
from filelisttest import FileListTest
from inboxtest import InboxTest
from logcomponenttest import LogComponentTest
from logobservertest import LogObserverTest
from packertest import PackerTest
from parsecqltest import ParseCQLTest
from persistentsortedintegerlisttest import PersistentSortedIntegerListTest
from reindextest import ReindexTest
from renamecqlindextest import RenameCqlIndexTest
from requestscopetest import RequestScopeTest
from rewritepartnametest import RewritePartnameTest
from rssitemtest import RssItemTest
from rsstest import RssTest
from sorteditertoolstest import SortedItertoolsTest
from statisticstest import StatisticsTest
from statisticsxmltest import StatisticsXmlTest
from storagecomponenttest import StorageComponentTest
from tokenizefieldlettest import TokenizeFieldletTest
from venturitest import VenturiTest
from xml2fieldstest import Xml2FieldsTest
from xmlpumptest import XmlPumpTest
from xpath2fieldtest import XPath2FieldTest

from autocomplete.autocompletetest import AutocompleteTest

from http.apacheloggertest import ApacheLoggerTest
from http.argumentsinsessiontest import ArgumentsInSessionTest
from http.basicauthenticationtest import BasicAuthenticationTest
from http.fileservertest import FileServerTest
from http.handlerequestfiltertest import HandleRequestFilterTest
from http.ipfiltertest import IpFilterTest
from http.observablehttpservertest import ObservableHttpServerTest
from http.pathfiltertest import PathFilterTest
from http.pathrenametest import PathRenameTest
from http.sessionhandlertest import SessionHandlerTest
from http.timeddictionarytest import TimedDictionaryTest
from http.utilstest import UtilsTest

from numeric.converttest import ConvertTest
from numeric.numbercomparitorfieldlettest import NumberComparitorFieldletTest
from numeric.numbercomparitormodifiertest import NumberComparitorModifierTest
from numeric.numbercomparitortest import NumberComparitorTest

from sru.srufielddrilldowntest import SRUFieldDrilldownTest
from sru.sruhandlertest import SruHandlerTest
from sru.sruparsertest import SruParserTest
from sru.srurecordupdatetest import SRURecordUpdateTest
from sru.srutermdrilldowntest import SRUTermDrilldownTest
from sru.srwtest import SrwTest

from xml_generic.lxml_based.crosswalktest import CrosswalkTest
from xml_generic.lxml_based.xmlcomposetest import XmlComposeTest
from xml_generic.lxml_based.xmlxpathtest import XmlXPathTest
from xml_generic.lxml_based.xsltcrosswalktest import XsltCrosswalkTest
from xml_generic.validatetest import ValidateTest

from facetindex.clausecollectortest import ClauseCollectorTest
from facetindex.cql2lucenequerytest import Cql2LuceneQueryTest
from facetindex.cqlparsetreetolucenequerytest import CqlParseTreeToLuceneQueryTest
from facetindex.docsetlisttest import DocSetListTest
from facetindex.docsetlistintersecttest import DocSetListIntersectTest
from facetindex.docsettest import DocSetTest
from facetindex.documenttest import DocumentTest
from facetindex.drilldowntest import DrilldownTest
from facetindex.drilldownfieldnamestest import DrilldownFieldnamesTest
from facetindex.fields2lucenedocumenttest import Fields2LuceneDocumentTest
from facetindex.incrementalindexingtest import IncrementalIndexingTest
from facetindex.integerlisttest import IntegerListTest
from facetindex.libfacetindextest import LibFacetIndexTest
from facetindex.lucenedocidtrackertest import LuceneDocIdTrackerTest
from facetindex.lucenetest import LuceneTest
from facetindex.pooltest import PoolTest
from facetindex.tools.lucenetoolstest import LuceneToolsTest
from facetindex.triedicttest import TrieDictTest
from facetindex.trietest import TrieTest

from ngram.cqlsuggestertest import CqlSuggesterTest
from ngram.cqltermvisitortest import CqlTermVisitorTest
from ngram.ngramindextest import NGramIndexTest
from ngram.ngramquerytest import NGramQueryTest
from ngram.ngramtest import NGramTest

from msgbox.msgboxtest import MsgboxTest
from msgbox.updateadaptertest import UpdateAdapterTest

from web.webquerytest import WebQueryTest

if __name__ == '__main__':
    unittest.main()
