#!/bin/bash
## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
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
