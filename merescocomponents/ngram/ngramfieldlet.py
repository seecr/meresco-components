# -*- coding: utf-8 -*-
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

from merescocore.framework import Transparant
from merescocomponents.facetindex import document
from PyLucene import TermQuery, Term
from math import log

from ngram import ngrams

APPEARS_FIELD = 'appears'

def ngramFieldname(name):
    return 'ngram_%s' % name

class NGramFieldlet(Transparant):
    """Fieldlet used in Meresco DNA to build/fill an NGram index used for
    suggestions."""
    def __init__(self, n, fieldName, fieldNames=None):
        Transparant.__init__(self)
        self._fieldName = fieldName
        self._fieldNames = fieldNames
        self._ngram = lambda word:ngrams(word, n)

    def addField(self, name, value):
        word = value
        count, fields = self.any.executeQueryWithField(TermQuery(Term(document.IDFIELD, word)), APPEARS_FIELD)
        appears = 1
        if count > 0:
            appears += int(fields[0]) if fields[0] else 0
            boost = log(appears)/10
        else:
            boost = 10**-6
        self.any.changeBoost(boost)
        self.ctx.tx.locals['id'] = word
        ngrams = ' '.join(self._ngram(word))
        self.do.addField(self._fieldName, ngrams)
        self.do.addField(name=APPEARS_FIELD, value=str(appears), store=True)
        if self._fieldNames and name in self._fieldNames:
            self.do.addField(name=ngramFieldname(name) , value=ngrams)

