## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012, 2016, 2019-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2016 SURFmarket https://surf.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from .observablehttpserver import ObservableHttpServer
#from .observablehttpsserver import ObservableHttpsServer
from .pathfilter import PathFilter
from .pathrename import PathRename
from .fileserver import StringServer, FileServer
from .ipfilter import IpFilter
from .basichttphandler import BasicHttpHandler
from .basicauthentication import BasicAuthentication
from .sessionhandler import SessionHandler
from .argumentsinsession import ArgumentsInSession
from .apachelogger import ApacheLogger
from .utils import insertHeader
from .handlerequestfilter import HandleRequestFilter
from .deproxy import Deproxy, OnlyDeproxied
from .httpclient import HttpClient
from .cookiestore import CookieMemoryStore, CookiePersistentStore
from .staticfiles import StaticFiles, libdirForPrefix
from .staticfilemapping import StaticFileMapping
