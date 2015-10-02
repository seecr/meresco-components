## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  initiated by Stichting Bibliotheek.nl to provide a new search service
#  for all public libraries in the Netherlands.
#
# Copyright (C) 2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
#
# This file is part of "NBC+ (Zoekplatform BNL)"
#
# "NBC+ (Zoekplatform BNL)" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "NBC+ (Zoekplatform BNL)" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "NBC+ (Zoekplatform BNL)"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from meresco.core import Observable


class DrilldownQueries(Observable):
    def executeQuery(self, extraArguments, **kwargs):
        drilldownQueries = []
        xDrilldownQueries = extraArguments.get('x-drilldown-query')
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
