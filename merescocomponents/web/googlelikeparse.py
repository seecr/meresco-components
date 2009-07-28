# -*- coding: utf-8 -*-

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

