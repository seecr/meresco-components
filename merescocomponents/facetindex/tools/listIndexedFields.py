#!/usr/bin/env python2.5
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
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

from PyLucene import IndexReader, Term
from sys import argv
from os.path import basename

def findFields(reader):
    return reader.getFieldNames(IndexReader.FieldOption.ALL)

def printFields(fields):
    for field in sorted(fields):
        print field

def listTerms(reader, fields, fieldName=''):
    termDocs = reader.termDocs()
    for field in sorted(fields):
        if field != fieldName:
            continue

        print field
        termEnum = reader.terms(Term(field, ''))
        while True:
            if termEnum.term().field() != field:
                break
            termDocs.seek(termEnum)
            docIds = []
            while termDocs.next():
                docIds.append(termDocs.doc())
            print termEnum.term().text(), len(docIds)
            if not termEnum.next():
                break
        print '\n'

if __name__ == '__main__':
    args = argv[1:]
    if len(args) < 1:
        print 'Usage: %s <index directory name> --fields | --terms <fieldname>' % basename(argv[0])
    else:
        index = args[0]
        reader = IndexReader.open(index)
        fields = findFields(reader)
        if '--fields' in args:
            printFields(fields)
        elif '--terms' in args:
            paramIndex = args.index('--terms')
            fieldName = ''
            if paramIndex+1 < len(args):
                fieldName = args[paramIndex+1]

            listTerms(reader, fields, fieldName=fieldName)

