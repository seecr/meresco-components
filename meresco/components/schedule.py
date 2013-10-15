## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2013 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2013 Maastricht University Library http://www.maastrichtuniversity.nl/web/Library/home.htm
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

from datetime import datetime

class Schedule(object):
    def __init__(self, period=None, timeOfDay=None, dayOfWeek=None):
        if (period and (timeOfDay or dayOfWeek)) or \
                (dayOfWeek and not timeOfDay):
            raise ValueError("specify either 'period' or 'timeOfDay' with optional 'dayOfWeek'")
        self._data = {
            'period': period,
            'timeOfDay': timeOfDay,
            'dayOfWeek': dayOfWeek,
        }

    @property
    def period(self):
        return self._data['period']

    @property
    def timeOfDay(self):
        return self._data['timeOfDay']

    @property
    def dayOfWeek(self):
        return self._data['dayOfWeek']

    def secondsFromNow(self):
        if self.period:
            return self.period

        targetTime = datetime.strptime(self.timeOfDay, "%H:%M")
        time = self._time()
        currentTime = datetime.strptime("%s:%s:%s" % (time.hour, time.minute, time.second), "%H:%M:%S")
        timeDelta = targetTime - currentTime
        daysDelta = 0
        if self.dayOfWeek:
            daysDelta = self.dayOfWeek - time.isoweekday() + timeDelta.days
            if daysDelta < 0:
                daysDelta += 7
        return daysDelta * 24 * 60 * 60 + timeDelta.seconds

    def _time(self):
        return datetime.utcnow()

    def __repr__(self):
        return "Schedule(%s)" % ', '.join('%s=%s' % (
            k,repr(v))
            for (k,v) in sorted(self._data.items())
            if v)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(tuple(sorted(self._data.items())))
