from ctypes import cdll
from os.path import join, abspath, dirname

import PyLucene # make sure PyLucene/Java is initialized before loading _docset.so

libFacetIndex = cdll.LoadLibrary(join(abspath(dirname(__file__)), '_facetindex.so'))
