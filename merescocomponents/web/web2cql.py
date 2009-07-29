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

import re
UNQUOTED_STRING = r'(?P<unquoted>[\+\-]?[^"\s]+)'
QUOTED_STRING = r'(?P<quotedString>[\+\-]?(?P<quot>\")(?P<quoted>.+?)((?<!\\)(?P=quot)))'
QUOTED_LABEL_STRING = r'(?P<labelString>[\+\-]?(?P<label>[^"\s]+)=(?P<quot1>\")(?P<quoted1>.+?)((?<!\\)(?P=quot1)))'
STRINGS = [QUOTED_LABEL_STRING ,QUOTED_STRING, UNQUOTED_STRING]

SPLITTED_STRINGS = re.compile(r'\s*(%s)' % '|'.join(STRINGS))

from cqlparser import parseString, CQLParseException

DEFAULT, PLUSMINUS, BOOLEAN = range(3)

class WebQuery(object):
    
    def __init__(self, aString, antiUnaryClause=""):
        plusminus = _feelsLikePlusMinusQuery(aString)
        boolean = _feelsLikeBooleanQuery(aString)
        self._needsHelp = boolean and plusminus
        if plusminus and not boolean:
            self._kind = PLUSMINUS
            self.ast = parseString(_plusminus2Cql(aString, antiUnaryClause))
        elif boolean and not plusminus:
            try:
                self._kind = BOOLEAN
                self.ast = parseString(_boolean2Cql(aString, antiUnaryClause))
            except CQLParseException:
                self._needsHelp = True
                self._kind = DEFAULT
                self.ast = parseString(_default2Cql(aString))              
        else:
            self._kind = DEFAULT
            self.ast = parseString(_default2Cql(aString))

    def addFilter(self, field, term):
        #pruts, pruts
        pass

    def isBooleanQuery(self):
        return self._kind == BOOLEAN

    def isPlusMinusQuery(self):
        return self._kind == PLUSMINUS

    def isDefaultQuery(self):
        return self._kind == DEFAULT

    def needsBooleanHelp(self):
        return self._needsHelp
        

def _feelsLikePlusMinusQuery(aString):
    for part in (_valueFromGroupdict(m.groupdict()).lower() for m in SPLITTED_STRINGS.finditer(aString)):
        if part[0] in ['-', '+']:
            return True
    return False

def _feelsLikeBooleanQuery(aString):
    for part in (_valueFromGroupdict(m.groupdict()).lower() for m in SPLITTED_STRINGS.finditer(aString)):
        if part in ['and', 'or', 'not']:
            return True
        elif part[0] == '(' or part[-1] == ')':
            return True
    return False

def _joinFieldAndTerm(fieldAndTermList):
    results = []
    for field, term in (tuple(fieldAndTerm.split(':', 1)) for fieldAndTerm in fieldAndTermList):
        if ' ' in term:
            term = '"%s"' % term
        results.append('%s exact %s' % (field, term))
    if len(results) == 1:
        return results[0]

    return ' AND '.join('(%s)' % result for result in results)

def _plusminus2Cql(aString, antiUnaryClause):
    newParts = []
    for match in SPLITTED_STRINGS.finditer(aString):
        part = _valueFromGroupdict(match.groupdict())
        if part[0] == '+':
            newParts.append(part[1:])
        elif part[0] == '-':
            notStatement = 'NOT ' + part[1:]

            if len(newParts) == 0:
                newParts.append(antiUnaryClause + " " + notStatement)
            else:
                newParts[-1] = newParts[-1] + ' ' + notStatement
        else:
            newParts.append(part)
    return ' AND '.join(newParts)

def _boolean2Cql(aString, antiUnaryClause):
    aString = aString.replace('(', ' ( ').replace(')', ' ) ')
    newParts = []
    for match in SPLITTED_STRINGS.finditer(aString):
        part = _valueFromGroupdict(match.groupdict())
        partAsToken = part.lower()
        if partAsToken == 'not':
            if len(newParts) == 0 or newParts[-1] == '(':
                newParts.append(antiUnaryClause)
        if partAsToken in ['not', 'and', 'or']:
            part = part.upper()
        newParts.append(part)
    return ' '.join(newParts)

def _default2Cql(aString, antiUnaryClause="ignored"):
    return ' AND '.join(quot(part) for part in aString.split())

def quot(aString):
    if aString[-1] == '"' == aString[0]:
        return aString
    return '"%s"' % aString

def _valueFromGroupdict(groupdict):
    return groupdict['unquoted'] or groupdict['quotedString'] or groupdict['labelString']

