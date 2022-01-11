## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2010, 2013, 2015-2016, 2018, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2011-2013, 2015-2016, 2018, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012-2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

usrSharePath = '/usr/share/meresco-components'
from os.path import dirname, abspath, join                #DO_NOT_DISTRIBUTE
mydir = dirname(abspath(__file__))                        #DO_NOT_DISTRIBUTE
usrSharePath = join(dirname(dirname(mydir)), 'usr-share') #DO_NOT_DISTRIBUTE

from ._utils import *

from .converter import Converter
from .timeddictionary import TimedDictionary
from .timedpersistentdictionary import TimedPersistentDictionary
from .xmlcompose import XmlCompose
from .xmlpump import XmlPrintLxml, XmlParseLxml, FileParseLxml, lxmltostring, lxmltobytes

from .berkeleydict import DoubleUniqueBerkeleyDict, BerkeleyDict
from .combineparts import CombineParts
from .configuration import Configuration, readConfig
from .contextset import ContextSetList, ContextSet
from .cqlconversion import CqlSearchClauseConversion, CqlMultiSearchClauseConversion
from .directorywatcher import DirectoryWatcher, DirectoryWatcherException
from .fieldlets import RenameField, TransformFieldValue, FilterFieldValue, FilterField, AddField
from .fields2xml import Fields2Xml
from .fields2xmlfields import Fields2XmlFields
from .filtermessages import FilterMessages
from .filterdatabyname import FilterDataByName
from .inbox import Inbox
from .iteratorasstream import IteratorAsStream
from .multileveldrilldown import MultiLevelDrilldown, MultiLevelDrilldownException
from .parsearguments import ParseArguments
from .periodiccall import PeriodicCall
from .periodicdownload import PeriodicDownload
from .renamecqlindex import RenameCqlIndex
from .renamefieldforexact import RenameFieldForExact
from .requestscope import RequestScope
from .rewritepartname import RewritePartname
from .rss import Rss
from .rssitem import RssItem
from .schedule import Schedule
from .timedmessagecache import TimedMessageCache, BackoffException
from .venturi import Venturi
from .xml2fields import Xml2Fields
from .xmlxpath import XmlXPath
from .xpath2field import XPath2Field
from .xsltcrosswalk import XsltCrosswalk
from .url import parseAbsoluteUrl
from .onlyadddeleteifchanged import OnlyAddDeleteIfChanged
from .retrievetogetdataadapter import RetrieveToGetDataAdapter
from .sortkeysrename import SortKeysRename


