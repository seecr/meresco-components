## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015-2016 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015-2017, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from seecr.zulutime import ZuluTime

from meresco.core.observable import Observable


class PacketToLog(Observable):
    def add(self, data):
        d = loglineToDict(data)
        yield self.all.logData(dataDict=d)


def loglineToDict(line):
    parts = line.split(' ') + ['']
    zulutime, ipAddress, size, duration, hits, path, arguments = parts[:7]
    return {
        'timestamp': int(ZuluTime(zulutime).epoch if 'Z' in zulutime else int(zulutime)),
        'ipAddress': ipAddress,
        'size': int(float(size[:-1]) * 1024) if size != '-' else None,
        'duration': int(float(duration.split('s')[0])*1000) if duration != '-' else None,
        'hits': int(hits.split('hits')[0]) if hits != '-' else None,
        'path': path,
        'arguments': arguments,
    }

def dictToLogline(dataDict):
    return ' '.join([
        ZuluTime.parseEpoch(int(dataDict['timestamp'])).zulu(),
        dataDict['ipAddress'],
        '-' if dataDict['size'] is None else ('%.1fK' % (dataDict['size'] / 1024.0)),
        '-' if dataDict['duration'] is None else ('%.3fs' % (dataDict['duration'] / 1000.0)),
        '-' if dataDict['hits'] is None else '%shits' % dataDict['hits'],
        dataDict['path'],
        dataDict['arguments'],
    ])
