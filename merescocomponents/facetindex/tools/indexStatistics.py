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

if len(argv) < 2:
    print 'Usage:', argv[0], '<path to index>'
    exit(0)

indexPath = argv[1]

from PyLucene import IndexReader

reader = IndexReader.open(indexPath)
numDocs = reader.numDocs()
print 'Opened', indexPath, 'with', numDocs, 'documents'
termDocs = reader.termDocs()
termEnum = reader.terms()
dfFreq = {}
stopwords = []
l, t, f = 0, 0, 0
while termEnum.next():
	term = termEnum.term()
	l += len(term.text())
	t += 1
	ft = termEnum.docFreq()
	dff = 100*ft/numDocs/10 * 10
	if dff not in dfFreq:
		dfFreq[dff] = 1
	else:
		dfFreq[dff] += 1
	if ft > numDocs*0.9:
		stopwords.append((term.text(), ft))
	f += ft
	if t % 10000 == 0: print 'Analyzing terms:', t, '\r',
	stdout.flush()
atl = float(l)/t
adf = float(f)/t
print 'Terms:', t, 'Average term lenght:', atl, 'Average doc freq:', adf
termDictSize = t * atl*16
matrixSize = t * adf*64
x64 = (termDictSize + matrixSize) /8 /1024 /1024 /1024
print 'With postings of 64 bits, an index would require', x64, 'GB.'
print 'TermDict:', termDictSize/8/1024/1024/1024, 'Matrix:', matrixSize/8/1024/1024/1024
print 'TF distributie'
for r in sorted(dfFreq.keys()):
	print 'from', r,'% :',dfFreq[r]
print 'Stopwords:', len(stopwords), 'save', sum(f for sw, f in stopwords)*64/8/1024/1024, 'MB'
for s, f in stopwords:
	print s, 100*f/numDocs, '%'
