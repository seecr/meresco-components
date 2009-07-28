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
UNQUOTED_STRING = r'(?P<unquoted>[\+|\-]?[^"\s]+)'
QUOTED_STRING = r'(?P<plusminus>[\+|\-]?)(?P<quot>\")(?P<quoted>.+?)((?<!\\)(?P=quot))'
QUOTED_LABEL_STRING = r'(?P<quotedLabel>\S+=(?P<quot1>\")(?P<quoted1>.+?)((?<!\\)(?P=quot1)))'
STRINGS = [QUOTED_LABEL_STRING ,QUOTED_STRING, UNQUOTED_STRING]

SPLITTED_STRINGS = re.compile(r'\s*(%s)' % '|'.join(STRINGS))

def unGoogleQuery(aString, antiUnaryClause=""):
    if isGoogleLikePlusMinusQuery(aString):
        return _unGooglePlusMinusQuery(aString, antiUnaryClause)
    elif isGoogleLikeBooleanQuery(aString):
        return _unGoogleBooleanQuery(aString, antiUnaryClause)
    return aString


def isGoogleLikeQuery(aString):
    return isGoogleLikeBooleanQuery(aString) or isGoogleLikePlusMinusQuery(aString)

def isGoogleLikePlusMinusQuery(aString):
    googleLike = False
    for part in aString.lower().split():
        if part in ['and', 'or', 'not']:
            googleLike = False
            break
        elif part[0] == '(' or part[-1] == ')':
            googleLike = False
            break
        elif part[0] in ['-', '+']:
            googleLike = True
    return googleLike

def isGoogleLikeBooleanQuery(aString):
    googleLike = False
    for part in aString.lower().split():
        if part[0] in ['-', '+']:
            googleLike = False
            break
        elif part in ['and', 'or', 'not']:
            googleLike = True
    return googleLike

def buildQuery(queryString, drilldownArguments):
    cqlQuery = queryString

    drilldownCqlString = _joinFieldAndTerm(drilldownArguments)
    if cqlQuery and drilldownCqlString:
        cqlQuery = '(%s) AND %s' % (cqlQuery, drilldownCqlString)
    elif cqlQuery == '' and drilldownCqlString:
        cqlQuery = drilldownCqlString

    return cqlQuery

def _joinFieldAndTerm(fieldAndTermList):
    results = []
    for field, term in (tuple(fieldAndTerm.split(':', 1)) for fieldAndTerm in fieldAndTermList):
        if ' ' in term:
            term = '"%s"' % term
        results.append('%s exact %s' % (field, term))
    if len(results) == 1:
        return results[0]

    return ' AND '.join('(%s)' % result for result in results)

def _unGooglePlusMinusQuery(aString, antiUnaryClause):
    newParts = []
    for match in SPLITTED_STRINGS.finditer(aString):
        part = _valueFromGroupdict(match.groupdict())
        if part[0] == '+':
            newParts.append(part[1:])
        elif part[0] == '-':
            notStatement = 'NOT ' + part[1:]

            if len(newParts) == 0:
                newParts.append('(' + antiUnaryClause + " " + notStatement + ')')
            else:
                newParts[-1] = '(' + newParts[-1] + ' ' + notStatement + ')'
        else:
            newParts.append(part)
    return ' AND '.join(newParts)

def _unGoogleBooleanQuery(aString, antiUnaryClause):
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


def _valueFromGroupdict(groupdict):
    if groupdict['unquoted'] != None:
        return groupdict['unquoted']
    if groupdict['quoted'] != None:
        plusminus = ''
        if groupdict['plusminus']:
            plusminus = groupdict['plusminus']
        return '%s"%s"' % (plusminus, groupdict['quoted'])
    raise ValueError('Nothing found')

