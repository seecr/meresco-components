#!/usr/bin/env python2.5

from sys import argv, path
from os.path import abspath, dirname, join
from glob import glob
from os import listdir

basepath=dirname(dirname(dirname(dirname(abspath(__file__)))))

for dep in glob(join(basepath, 'deps.d/*')):
    path.insert(0, dep)
path.insert(0, basepath)

from PyLucene import IndexWriter
from merescocomponents.facetindex.lucene import IncludeStopWordAnalyzer
from lucenetools import unlock

def optimize(path):
    unlock(path)
    writer = IndexWriter(path, IncludeStopWordAnalyzer(), False)
    writer.optimize()
    writer.close()


if __name__ == '__main__':
    args = argv[1:]
    if not args:
        print "Specify index directory"
    else:
        optimize(args[0])