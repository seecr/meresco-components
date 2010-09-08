#!/bin/bash
#MACHINE=`gcc -dumpmachine`
#GCCVERSION=`gcc -dumpversion`
#GCCVERSION_SHORT=$(echo $GCCVERSION | awk -F. '{print $1"."$2}')
#
#LIBRARY_PATH=/usr/lib/gcc/$MACHINE/${GCCVERSION} \
#CPLUS_INCLUDE_PATH=/usr/include/c++/${GCCVERSION}:/usr/lib/gcc/$MACHINE/${GCCVERSION}/include \
#CPP=cpp-${GCCVERSION_SHORT} CC=gcc-${GCCVERSION_SHORT} CXX=g++-${GCCVERSION_SHORT} python2.5 setup.py build_ext --inplace

ARGS="$@"
if [ -z "${ARGS}" ]; then
    # For building a local checked-out code
    ARGS="build_ext --inplace"
fi

GCCDIR=/opt/gcc-4.3.2
MACHINE=`${GCCDIR}/bin/gcc -dumpmachine`
GCCVERSION=`${GCCDIR}/bin/gcc -dumpversion`
GCCVERSION_SHORT=$(echo $GCCVERSION | awk -F. '{print $1"."$2}')

LIBRARY_PATH=${GCCDIR}/lib/gcc/$MACHINE/${GCCVERSION} \
CPLUS_INCLUDE_PATH=${GCCDIR}/include/c++/${GCCVERSION}:${GCCDIR}/lib/gcc/$MACHINE/${GCCVERSION}/include \
CPP=cpp-${GCCVERSION_SHORT} CC=gcc-${GCCVERSION_SHORT} CXX=g++-${GCCVERSION_SHORT} python2.5 setup.py ${ARGS}
