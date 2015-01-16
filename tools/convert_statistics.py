#!/usr/bin/env python
# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from sys import argv
from os.path import isfile

def convert_pickle_file(pickle_file):
    target = "%s.converted" % pickle_file
    if isfile(target):
        print("File '%s' already exists" % target)
        return
       
    with open(pickle_file, "rb") as fp:
        contents = fp.read()
    converted = contents.replace(b'merescocore.components.statistics', b'meresco.components.statistics')
    
    with open(target, 'wb') as fp:
        fp.write(converted)
    return target

if __name__ == '__main__':
    args = argv[1:]
    if args == []:
        print("Usage: %s <pickle-file>" % argv[0])
        exit(1)

    if not isfile(args[0]):
        print("File '%s' not found" % args[0])
        exit(1)
    convert_pickle_file(args[0])
