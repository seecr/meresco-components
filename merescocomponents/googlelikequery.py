## begin license ##
#
#    "Delft-Tilburg" (delfttilburg) is a package containing shared code
#    between the Delft "Discover" and Tilburg "Beter Zoeken & Vinden" projects.
#    Both projects are based on Meresco Software (http://meresco.com)
#    Copyright (C) 2008-2009 Technische Universiteit Delft http://www.tudelft.nl
#    Copyright (C) 2008-2009 Universiteit van Tilburg http://www.uvt.nl
#    Copyright (C) 2008-2009 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of "Delft-Tilburg".
#
#    "Delft-Tilburg" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "Delft-Tilburg" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "Delft-Tilburg"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from cqlparser import parseString, CQLParseException
import re

UNQUOTED_STRING = r'(?P<unquoted>[^"\s]+)'
QUOTED_STRING = r'(?P<quot>\")(?P<quoted>.+?)((?<!\\)(?P=quot))'
QUOTED_LABEL_STRING = r'(?P<quotedLabel>\S+=(?P<quot1>\")(?P<quoted1>.+?)((?<!\\)(?P=quot1)))'
STRINGS = [QUOTED_LABEL_STRING ,UNQUOTED_STRING, QUOTED_STRING]

SPLITTED_STRINGS = re.compile(r'\s*(%s)' % '|'.join(STRINGS))

def createAndQuery(queryString):
    terms = []
    for rawterm in SPLITTED_STRINGS.finditer(queryString):
        result = rawterm.groupdict()
        if result['unquoted']:
            term = result['unquoted']
            if term.lower() in ['and', 'or'] or term[-1] == '=':
                term = '"%s"' % term
        elif result['quoted']:
            quote = result['quot']
            term = quote + result['quoted'] + quote
        elif result['quotedLabel']:
            term = result['quotedLabel']
        if term[0] == '(' or term[-1] == ')':
            term = '"%s"' % term
        terms.append(term)

    return ' AND '.join(terms)

def _joinFieldAndTerm(fieldAndTermList):
    results = []
    for field, term in (tuple(fieldAndTerm.split(':', 1)) for fieldAndTerm in fieldAndTermList):
        if ' ' in term:
            term = '"%s"' % term
        results.append('%s exact %s' % (field, term))
    if len(results) == 1:
        return results[0]

    return ' AND '.join('(%s)' % result for result in results)

def buildQuery(queryString, drilldownArguments, extra):
    cqlQuery = queryString

    drilldownCqlString = _joinFieldAndTerm(drilldownArguments)
    extraCqlString = _joinFieldAndTerm(extra) if extra else ''

    if drilldownCqlString and not extraCqlString:
        cqlQuery = '(%s) AND %s' % (cqlQuery, drilldownCqlString)
    elif not drilldownCqlString and extraCqlString:
        cqlQuery = '(%s) AND %s' % (cqlQuery, extraCqlString)
    elif drilldownCqlString and extraCqlString:
        cqlQuery = '(%s) AND (%s) AND (%s)' % (cqlQuery, drilldownCqlString, extraCqlString)

    return cqlQuery


def createParseTree(queryString, drilldownArguments, extra):
    cqlQuery = buildQuery(queryString, drilldownArguments, extra)
    cqlQuery = cqlQuery != None and str(cqlQuery) or ''

    return parseString(cqlQuery), cqlQuery

def unGoogleQuery(aString, antiUnaryClause=""):
    source = aString.replace('(', '( ')
    parts = source.split()
    for index, part in enumerate(parts):
        if part[0] =='-' and len(part) > 1:
            parts[index] = parts[index][1:]
            parts.insert(index, 'NOT')
            if index == 0 or parts[index-1] == '(':
                parts.insert(index, antiUnaryClause)
    return ' '.join(parts).replace('( ', '(')

def isGoogleLikeQuery(aString):
    googleLike = False
    for part in aString.lower().split():
        if part in ['and', 'or']:
            googleLike = True
        elif part[0] in ['(', '-'] or part[-1] == ')':
            googleLike = True

    return googleLike

def isValidGoogleQuery(googleQuery):
    try:
        parseString(unGoogleQuery(googleQuery, antiUnaryClause='meresco.exists exact true'))
    except Exception, e:
        return False
    return True

def parseQuery(httpQuery, drilldownArguments, extra=None):
    queryString = httpQuery
    googleQuery = isGoogleLikeQuery(queryString) and isValidGoogleQuery(queryString)
    queryString = unGoogleQuery(queryString, antiUnaryClause='meresco.exists exact true') if googleQuery else createAndQuery(queryString)

    return createParseTree(queryString if queryString else 'meresco.exists exact true', drilldownArguments, extra)

class GoogleLikeQuery(object):

    def parseQuery(self, httpQuery, drilldownArguments, extra=None):
        return parseQuery(httpQuery, drilldownArguments, extra=extra)

    def isGoogleLikeQuery(self, aString):
        return isGoogleLikeQuery(aString)

    def isValidGoogleQuery(self, aString):
        return isValidGoogleQuery(aString)