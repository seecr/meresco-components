#!/bin/bash
set -e

rm -rf tmp build
MACHINE=`gcc -dumpmachine`
GCCVERSION=`gcc -dumpversion`
GCCVERSION_SHORT=$(echo $GCCVERSION | awk -F. '{print $1"."$2}')

LIBRARY_PATH=/usr/lib/gcc/$MACHINE/${GCCVERSION} \
CPLUS_INCLUDE_PATH=/usr/include/c++/${GCCVERSION}:/usr/lib/gcc/$MACHINE/${GCCVERSION}/include \
CPP=cpp-${GCCVERSION_SHORT} CC=gcc-${GCCVERSION_SHORT} CXX=g++-${GCCVERSION_SHORT} python2.5 setup.py install --root tmp

cp meresco/__init__.py tmp/usr/lib/python2.5/site-packages/meresco
export PYTHONPATH=`pwd`/tmp/usr/lib/python2.5/site-packages
cp -r test tmp/test

(
cd tmp/test
./alltests.sh
)

rm -rf tmp build
