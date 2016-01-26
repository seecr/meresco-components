## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2016 Stichting Kennisnet http://www.kennisnet.nl
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

class LogLine(object):
    def __init__(self, *keys):
        self._keys = keys

    @classmethod
    def createDefault(cls):
        return cls('timestamp', 'ipAddress', 'size', 'duration', 'numberOfRecords', 'path', 'queryArguments')

    def log(self, aDict):
        line = []
        for key in self._keys:
            line.append(valueForKey[key](aDict))
        return '%s\n' % ' '.join(line)

    def __call__(self, aDict):
        return self.log(aDict)

def _valueFromDict(aDict, key, template='%s', alt='-'):
    try:
        return template % aDict[key]
    except (TypeError, KeyError):
        return alt


valueForKey = {
    'timestamp': lambda d: strftime('%Y-%m-%dT%H:%M:%SZ', gmtime(d['timestamp'])),
    'ipAddress': lambda d: d.get('ipAddress', '-'),
    'size': lambda d: _valueFromDict(d, 'size', '%.1fK'),
    'duration': lambda d: _valueFromDict(d, 'duration', '%.3fs'),
    'numberOfRecords': lambda d: _valueFromDict(d, 'numberOfRecords', '%dhits'),
    'path': lambda d: d.get('path', '-'),
    'status': lambda d: d.get('status', '-'),
    'queryArguments': lambda d: '%s' % d.get('queryArguments', '')
}
