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
#    Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
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
from os.path import dirname, abspath, isdir, join            #DO_NOT_DISTRIBUTE
if isdir(join(abspath(dirname(__file__)), '.svn')):          #DO_NOT_DISTRIBUTE
    from os import system                                    #DO_NOT_DISTRIBUTE
    status = system("cd %s/../..; ./setup.sh"  % abspath(dirname(__file__)))  #DO_NOT_DISTRIBUTE
    if status > 0:                                           #DO_NOT_DISTRIBUTE
        import sys                                           #DO_NOT_DISTRIBUTE
        sys.exit(status)                                     #DO_NOT_DISTRIBUTE
                                                             #DO_NOT_DISTRIBUTE

from lucene import LuceneIndex
from drilldown import Drilldown
from document import Document, IDFIELD, DocumentException
from docset import DocSet
from docsetlist import DocSetList
from integerlist import IntegerList
from trie import Trie
from cql2lucenequery import CQL2LuceneQuery
from fields2lucenedocument import Fields2LuceneDocumentTx
from clausecollector import ClauseCollector
import merescolucene

