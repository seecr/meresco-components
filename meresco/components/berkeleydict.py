# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2007-2009 Kennisnet http://www.kennisnet.nl
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2012, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 Stichting Kennisnet https://www.kennisnet.nl
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

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='bsddb3')

from bsddb3 import btopen
from os.path import join

class BerkeleyDict(object):
    def __init__(self, directory):
        self._keyvalueDict = btopen(join(directory, 'keyvalue'))

    def __contains__(self, key):
        return self._keyvalueDict.__contains__(key)

    def __setitem__(self, key, value):
        self._keyvalueDict.__setitem__(key, value)
        self._keyvalueDict.sync()

    def __getitem__(self, key):
        return self._keyvalueDict.__getitem__(key)

    def __delitem__(self, key):
        self._keyvalueDict.__delitem__(key)
        self._keyvalueDict.sync()

    def get(self, key, default=None):
        return self._keyvalueDict.get(key, default=default)

class DoubleUniqueBerkeleyDict(BerkeleyDict):
    """Berkeley based dictionary where both key and value must be unique"""
    def __init__(self, directory):
        BerkeleyDict.__init__(self, directory)
        self._valuekeyDict = btopen(join(directory, 'valuekey'))

    def __setitem__(self, key, value):
        BerkeleyDict.__setitem__(self, key, value)
        self._valuekeyDict.__setitem__(value, key)
        self._valuekeyDict.sync()

    def __delitem__(self, key):
        value = self[key]
        BerkeleyDict.__delitem__(self, key)
        self._valuekeyDict.__delitem__(value)
        self._valuekeyDict.sync()

    def getKeyFor(self, value):
        return self._valuekeyDict.get(value, None)

