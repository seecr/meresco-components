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

from io import StringIO
from lxml.etree import parse, XMLParser, _ElementTree
from meresco.xml import XMLRewrite
from glob import glob
from os.path import basename, dirname, abspath, join

from meresco.core import Observable

EXTENSION = '.rules'

def rewriteRules(pattern, replacement, rules):
    return [rewrite(pattern, replacement, rule) for rule in rules]

def rewrite(pattern, replacement, rules):
    if type(rules) == str:
        return rules.replace(pattern, replacement)
    if type(rules) == tuple:
        return tuple(rewrite(pattern, replacement, rule) for rule in  rules)
    return rules

class Crosswalk(Observable):
    def __init__(self, argumentKeyword = None, rulesDir=join(abspath(dirname(__file__)), 'rules'), extraGlobals={}):
        assert argumentKeyword == None, 'Crosswalk converts any argument that looks like an Lxml ElementTree, usage of argumentKeyword is forbidden.'

        Observable.__init__(self)
        self.ruleSet = {}
        self.rulesDir = rulesDir
        self._globs = {}
        self._globs.update(extraGlobals)
        self._globs['rewriteRules']= rewriteRules

        if rulesDir:
            for fileName in glob(rulesDir + '/*' + EXTENSION):
                args = {}
                self.readConfig(basename(fileName[:-len(EXTENSION)]), args)
                self.ruleSet[args['inputNamespace']] = args
                del args['inputNamespace']

    def readConfig(self, ruleSetName, localsDict):
        self._globs['extend']= lambda name: self.readConfig(name, localsDict)
        exec(compile(open(self.rulesDir + '/' + ruleSetName + EXTENSION).read(), self.rulesDir + '/' + ruleSetName + EXTENSION, 'exec'), self._globs, localsDict)

    def _detectAndConvert(self, anObject):
        if type(anObject) == _ElementTree:
            return self.convert(anObject)
        return anObject

    def all_unknown(self, method, *args, **kwargs):
        newArgs = [self._detectAndConvert(arg) for arg in args]
        newKwargs = dict((key, self._detectAndConvert(value)) for key, value in list(kwargs.items()))
        yield self.all.unknown(method, *newArgs, **newKwargs)

    def convert(self, lxmlNode):
        if type(lxmlNode) == _ElementTree:
            prefix = lxmlNode.getroot().prefix
            nsmap = lxmlNode.getroot().nsmap
        else:
            prefix = lxmlNode.prefix
            nsmap = lxmlNode.nsmap
        if not prefix in nsmap:
            raise Exception("Prefix '%s' not found in rules, available namespaces: %s" % (prefix, list(nsmap.keys())))
        namespaceURI = nsmap[prefix]
        rewrite = XMLRewrite(lxmlNode, **self.ruleSet[namespaceURI])
        rewrite.applyRules()
        return rewrite.asLxml()

    def __str__(self):
        return 'CrosswalkComponent'
