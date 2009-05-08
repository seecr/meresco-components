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
from sys import argv, stdout
from PyLucene import IndexReader, Term
B  = 1
KB = 1024
MB = 1024*KB
GB = 1024*MB

ESTIMATED_OVERHEAD = 2
ESTIMATED_BYTES_POSTING  = 20 * ESTIMATED_OVERHEAD * B
ESTIMATED_BYTES_PER_TERM = 40 * ESTIMATED_OVERHEAD * B
ESTIMATED_RECORD_SIZE    = 12 * KB
BUFFERS_PERCENTAGE       = 10
HEADROOM_PERCENTAGE      = 25

if len(argv) < 2:
    print 'Usage:', argv[0], '<path to index>', '[fieldnameprefix]'
    exit(0)

indexPath = argv[1]
fieldnameprefix = argv[2] if len(argv) > 2 else ''

def printLine(caption, value, unit=''):
    print "%35s : %s %s            " % (caption, value, unit)

reader = IndexReader.open(indexPath)
numDocs = reader.numDocs()

fields = [field for field in reader.getFieldNames(IndexReader.FieldOption.ALL)
            if field.startswith(fieldnameprefix)]


print '=========='*6
printLine('Number of documents', numDocs)
printLine('Number of fields', len(fields))
dfFreq = {}
stopwords = []
totalTermLen, totalTermCount, postings = 0, 0, 0


for field in fields:
    termEnum = reader.terms(Term(field, ''))
    stdout.flush()
    while True:
        if termEnum.term().field() != field:
            break
        docFreq = termEnum.docFreq()
        term = termEnum.term()
        totalTermLen += len(term.text())
        totalTermCount += 1
        docFreq = termEnum.docFreq()
        postings += docFreq
        dff = 100*docFreq/numDocs/10 * 10
        if dff not in dfFreq:
            dfFreq[dff] = 1
        else:
            dfFreq[dff] += 1
        if docFreq > numDocs*0.9:
            stopwords.append((term.text(), docFreq))
        if totalTermCount % 10000 == 0:
            print field, totalTermCount, '                               \r',
            stdout.flush()
        if not termEnum.next():
            break

averageTermLen = totalTermLen/totalTermCount
averageDocFreq = postings/totalTermCount

printLine('Number of Terms', totalTermCount)
printLine('Average term length', averageTermLen, 'characters')
printLine('Number of postings', postings/10**6, 'miljoen')
printLine('Average doc freq', averageDocFreq, 'doc/term')

indexSize = postings * ESTIMATED_BYTES_POSTING
dictionarySize = totalTermCount * ESTIMATED_BYTES_PER_TERM
totalFacetIndexSize = indexSize+dictionarySize
printLine('Estimated size of index', indexSize/MB, 'MB')
printLine('Estimated size of dictionary', dictionarySize/MB, 'MB')
printLine('Estimated total size', totalFacetIndexSize/MB, 'MB')

roomForLucene = totalFacetIndexSize # equals FacetIndex
cacheAndBuffers = BUFFERS_PERCENTAGE * numDocs * ESTIMATED_RECORD_SIZE / 100
minimumMemory = totalFacetIndexSize + roomForLucene + cacheAndBuffers
printLine('Suggested room for Lucene', (indexSize+dictionarySize)/MB, 'MB')
printLine('Suggested for caching and buffers', cacheAndBuffers/MB, 'MB')
printLine('Suggested minimum memory', minimumMemory/MB, 'MB')

suggestedHeadRoom = HEADROOM_PERCENTAGE * minimumMemory / 100
suggestedPhysicalRAMinGB = (minimumMemory + suggestedHeadRoom)/GB
printLine('Suggested head room', suggestedHeadRoom/MB, 'MB')
printLine('Suggested physical RAM', suggestedPhysicalRAMinGB, 'GB')
print '=========='*6

if reader.isOptimized():
    print 'TF distributie'
    for r in sorted(dfFreq.keys()):
        print 'from', r,'% :',dfFreq[r]
    print 'Stopwords:', len(stopwords), 'save', sum(f for sw, f in stopwords)*64/8/MB, 'MB'
    for s, f in stopwords:
        print s, 100*f/numDocs, '%'
else:
    print "Optimize index for term frequency distribution and stopwords."
