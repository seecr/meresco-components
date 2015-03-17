# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2006-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2006-2012, 2014 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from time import strftime, gmtime
from os.path import join, isdir, isfile
from os import makedirs, listdir, remove

NR_OF_FILES_KEPT = 14

# '2009-11-02T11:30:00Z 127.0.0.1 0.0K 1.000s #123 /sru query=query&operation=searchRetrieve&version=1.1\n'
def _valueFromDict(aDict, key, template='%s', alt='-'):
    try:
        return template % aDict[key]
    except (TypeError, KeyError):
        return alt

def logline(aDict):
    line = []
    line.append(strftime('%Y-%m-%dT%H:%M:%SZ', gmtime(aDict['timestamp'])))
    line.append(aDict.get('ipAddress', '-'))
    line.append(_valueFromDict(aDict, 'size', '%.1fK'))
    line.append(_valueFromDict(aDict, 'duration', '%.3fs'))
    line.append(_valueFromDict(aDict, 'numberOfRecords', '%dhits'))
    line.append(aDict.get('path', '-'))
    line.append('%s' % aDict.get('queryArguments', ''))
    return '%s\n' % ' '.join(line)


logtemplate = '%(strTimestamp)s %(ipAddress)s %(size).1fK %(duration).3fs %(path)s %(queryArguments)s\n'

class DirectoryLog(object):
    def __init__(self, logdir, extension='-query.log', nrOfFilesKept=NR_OF_FILES_KEPT):
        self._previousLog = None
        self._logdir = logdir
        if not isdir(self._logdir):
            makedirs(self._logdir)
        self._filenameExtension = extension
        self._nrOfFilesKept = nrOfFilesKept

    def setNrOfFilesKept(self, value):
        if value > 0:
            self._nrOfFilesKept = value

    def _filename(self, timestamp):
        date = strftime('%Y-%m-%d', gmtime(timestamp))
        return join(self._logdir, '%s%s' % (date, self._filenameExtension))

    def log(self, **kwargs):
        timestamp = kwargs['timestamp']
        logFilename = self._filename(timestamp)

        if logFilename != self._previousLog:
            logs = self._logfiles()
            while len(logs) >= self._nrOfFilesKept:
                remove(join(self._logdir, logs[0]))
                logs = self._logfiles()
            self._previousLog = logFilename

        with open(logFilename, 'a') as f:
            f.write(logline(kwargs))

    def _logfiles(self):
        return sorted(f for f in listdir(self._logdir) if f.endswith(self._filenameExtension))

    def logExists(self, logName):
        return isfile(join(self._logdir, logName))

    def listlogs(self):
        return listdir(self._logdir)

    def getlog(self, logName):
        logFilename = join(self._logdir, logName)
        with open(logFilename) as f:
            for line in f:
                yield line


