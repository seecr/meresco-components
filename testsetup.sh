#!/bin/bash
set -e

rm -rf tmp build
fullPythonVersion=python2.6
MACHINE=`gcc -dumpmachine`
GCCVERSION=`gcc -dumpversion`
GCCVERSION_SHORT=$(echo $GCCVERSION | awk -F. '{print $1"."$2}')

LIBRARY_PATH=/usr/lib/gcc/$MACHINE/${GCCVERSION} \
CPLUS_INCLUDE_PATH=/usr/include/c++/${GCCVERSION}:/usr/lib/gcc/$MACHINE/${GCCVERSION}/include \
CPP=cpp-${GCCVERSION_SHORT} CC=gcc-${GCCVERSION_SHORT} CXX=g++-${GCCVERSION_SHORT} ${fullPythonVersion} setup.py install --root tmp

cp meresco/__init__.py tmp/usr/local/lib/${fullPythonVersion}/dist-packages/meresco
export PYTHONPATH=`pwd`/tmp/usr/local/lib/${fullPythonVersion}/dist-packages
cp -r test tmp/test

(
cd tmp/test
./alltests.sh
)

rm -rf tmp build

