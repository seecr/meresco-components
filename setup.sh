#!/bin/bash
MACHINE=`gcc -dumpmachine`
GCCVERSION=`gcc -dumpversion`
GCCVERSION_SHORT=$(echo $GCCVERSION | awk -F. '{print $1"."$2}')

LIBRARY_PATH=/usr/lib/gcc/$MACHINE/${GCCVERSION} \
CPLUS_INCLUDE_PATH=/usr/include/c++/${GCCVERSION}:/usr/lib/gcc/$MACHINE/${GCCVERSION}/include \
CPP=cpp-${GCCVERSION_SHORT} CC=gcc-${GCCVERSION_SHORT} CXX=g++-${GCCVERSION_SHORT} python2.5 setup.py build_ext --inplace
