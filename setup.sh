#!/bin/bash
MACHINE=`gcc -dumpmachine`
LIBRARY_PATH=/usr/lib/gcc/$MACHINE/4.1.2 \
CPLUS_INCLUDE_PATH=/usr/include/c++/4.1.2:/usr/lib/gcc/$MACHINE/4.1.2/include \
CPP=cpp-4.1 CC=gcc-4.1 CXX=g++-4.1 python2.5 setup.py build_ext --inplace
