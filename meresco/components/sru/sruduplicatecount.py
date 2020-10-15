## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2014, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

class SruDuplicateCount(object):

    def extraRecordData(self, hit):
        if not hasattr(hit, 'duplicateCount'):
            return
        for item in hit.duplicateCount.items():
            yield "<meresco_srw:duplicateCount fieldname='%s'>%s</meresco_srw:duplicateCount>" % item

    def extraResponseData(self, response, **kwargs):
        totalWithDuplicates = getattr(response, "totalWithDuplicates", None)
        if totalWithDuplicates is not None:
            yield "<meresco_srw:numberOfRecordsWithDuplicates>%s</meresco_srw:numberOfRecordsWithDuplicates>" % totalWithDuplicates
