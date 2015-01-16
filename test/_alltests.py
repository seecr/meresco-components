# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2010-2014 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2011-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from os import getuid
assert getuid() != 0, "Do not run tests as 'root'"

from seecr.deps import includeParentAndDeps         #DO_NOT_DISTRIBUTE
includeParentAndDeps(__file__)                      #DO_NOT_DISTRIBUTE

import unittest
from warnings import simplefilter
simplefilter('default')

from berkeleydicttest import DoubleUniqueBerkeleyDictTest, BerkeleyDictTest
from clausecollectortest import ClauseCollectorTest
from combinepartstest import CombinePartsTest
from contextsettest import ContextSetTest
from convertertest import ConverterTest
from cqlconversiontest import CQLConversionTest
from crosswalktest import CrosswalkTest
from datapumptest import DataPumpTest
from directorywatchertest import DirectoryWatcherTest
from fieldletstest import FieldletsTest
from fields2xmlfieldstest import Fields2XmlFieldsTest
from fields2xmltest import Fields2XmlTest
from filtermessagestest import FilterMessagesTest
from filterpartbynametest import FilterPartByNameTest
from inboxtest import InboxTest
from iteratorasstreamtest import IteratorAsStreamTest
from jsontest import JsonTest
from multileveldrilldowntest import MultiLevelDrilldownTest
from parseargumentstest import ParseArgumentsTest
from parsecqltest import ParseCQLTest
#from periodiccalltest import PeriodicCallTest
from periodicdownloadtest import PeriodicDownloadTest
#from persistentsortedintegerlisttest import PersistentSortedIntegerListTest
from reindextest import ReindexTest
from renamecqlindextest import RenameCqlIndexTest
from renamefieldforexacttest import RenameFieldForExactTest
from requestscopetest import RequestScopeTest
from rewritepartnametest import RewritePartnameTest
from rssitemtest import RssItemTest
from rsstest import RssTest
from scheduletest import ScheduleTest
from sorteditertoolstest import SortedItertoolsTest
from statisticstest import StatisticsTest
from statisticsxmltest import StatisticsXmlTest
from storagecomponenttest import StorageComponentTest
from tokenizefieldlettest import TokenizeFieldletTest
from venturitest import VenturiTest
from xml2fieldstest import Xml2FieldsTest
from xmlcomposetest import XmlComposeTest
from xmlpumptest import XmlPumpTest
from xmlxpathtest import XmlXPathTest
from xpath2fieldtest import XPath2FieldTest
from xsltcrosswalktest import XsltCrosswalkTest

from cql.searchtermfilterandmodifiertest import SearchTermFilterAndModifierTest

from autocomplete.autocompletetest import AutocompleteTest

from drilldown.srufielddrilldowntest import SruFieldDrilldownTest
from drilldown.srutermdrilldowntest import SruTermDrilldownTest
from drilldown.translatedrilldownfieldnamestest import TranslateDrilldownFieldnamesTest

from _http.apacheloggertest import ApacheLoggerTest
from _http.argumentsinsessiontest import ArgumentsInSessionTest
from _http.basicauthenticationtest import BasicAuthenticationTest
#from .http.basichttphandlertest import BasicHttpHandlerTest
#from .http.deproxytest import DeproxyTest
#from .http.fileservertest import FileServerTest
#from .http.handlerequestfiltertest import HandleRequestFilterTest
#from .http.httpclienttest import HttpClientTest
#from .http.ipfiltertest import IpFilterTest
#from .http.observablehttpservertest import ObservableHttpServerTest
#from .http.observablehttpsservertest import ObservableHttpsServerTest
#from .http.pathfiltertest import PathFilterTest
#from .http.pathrenametest import PathRenameTest
#from .http.sessionhandlertest import SessionHandlerTest
#from .http.timeddictionarytest import TimedDictionaryTest
#from .http.utilstest import UtilsTest

#from .log.apachelogwritertest import ApacheLogWriterTest
#from .log.directorylogtest import DirectoryLogTest
#from .log.handlerequestlogtest import HandleRequestLogTest
#from .log.logcollectortest import LogCollectorTest
#from .log.logfileservertest import LogFileServerTest
#from .log.querylogtest import QueryLogTest
#from .log.querylogwritertest import QueryLogWriterTest
#from .log.srulogtest import SruLogTest

#from .numeric.converttest import ConvertTest

#from .sru.sruhandlertest import SruHandlerTest
#from .sru.sruparsertest import SruParserTest
#from .sru.srurecordupdatetest import SruRecordUpdateTest
#from .sru.sruupdateclienttest import SruUpdateClientTest
#from .sru.srulimitstartrecordtest import SruLimitStartRecordTest
#from .sru.srwtest import SrwTest

#from .suggestion.suggestiontest import SuggestionTest

#from .xml_generic.validatetest import ValidateTest

#from .integerlist.integerlisttest import IntegerListTest

#from .ngram.cqlsuggestertest import CqlSuggesterTest
#from .ngram.cqltermvisitortest import CqlTermVisitorTest

#from .msgbox.msgboxtest import MsgboxTest
#from .msgbox.updateadaptertest import UpdateAdapterTest

#from .web.webquerytest import WebQueryTest

if __name__ == '__main__':
    unittest.main()
