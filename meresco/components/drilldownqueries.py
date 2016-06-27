## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014, 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from meresco.core import Observable


class DrilldownQueries(Observable):
    def executeQuery(self, extraArguments=None, **kwargs):
        drilldownQueries = []
        xDrilldownQueries = extraArguments.get('x-drilldown-query') if extraArguments else None
        if xDrilldownQueries:
            for q in xDrilldownQueries:
                if '=' in q:
                    field, value = q.split('=', 1)
                elif ' exact ' in q:
                    field, value = q.split(' exact ', 1)
                else:
                    raise ValueError("x-drilldown-query format should be field=value")
                drilldownQueries.append((field.strip(), [value.strip()]))
        response = yield self.any.executeQuery(extraArguments=extraArguments, drilldownQueries=drilldownQueries, **kwargs)
        raise StopIteration(response)
