## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

class Util(object):
    VALUES = "0123456789abcdefghijklmnopqrstuvwxy"
    def __init__(self, valueLength, base = 10):
        self.valueLength = valueLength
        self.base = base
        self.maximum = base ** valueLength

    def template(self, decimalPosition):
        return 'z' * (self.valueLength - decimalPosition - 1) + '%s' + 'z' * decimalPosition

    def decimal(self, value, decimalPosition):
        return value // self.base ** decimalPosition % self.base

    def termForPosition(self, value, decimalPosition):
        return self.termWithDecimal(self.decimal(value, decimalPosition), decimalPosition)

    def termWithDecimal(self, decimal, decimalPosition):
        return 'z' * (self.valueLength - decimalPosition - 1) +\
            self.VALUES[decimal] + \
            'z' * decimalPosition
