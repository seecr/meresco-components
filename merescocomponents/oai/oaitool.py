## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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

from time import strptime

class ISO8601Exception(Exception):
    pass

shortDate = '%Y-%m-%d'
longDate = '%Y-%m-%dT%H:%M:%SZ'

class ISO8601:
    short, long = [len('YYYY-MM-DD'), len('YYYY-MM-DDThh:mm:ssZ')]

    def __init__(self, s):
        if not len(s) in [self.short, self.long]:
            raise ISO8601Exception(s)
        
        if not self._matchesDateTimeFormat(shortDate, s) and not self._matchesDateTimeFormat(longDate, s):
          raise ISO8601Exception(s)
        self.s = s
    
    def _extend(self, extension):
        if not self.isShort():
            return self.s
        return self.s + extension

    def _matchesDateTimeFormat(self, aDateFormat, aDateString):
      result = True
      try:
        year, month, day, hour, minute, seconds, wday, yday, isdst = strptime(aDateString, aDateFormat)
        if seconds > 59:
          result = False
      except ValueError:
        result = False
      return result

    def floor(self):
        return self._extend("T00:00:00Z")
    
    def ceil(self):
        return self._extend("T23:59:59Z")
    
    def __str__(self):
        return self.floor()
    
    def isShort(self):
        return len(self.s) == self.short

