#!/bin/bash
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2012-2013, 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015 Stichting Kennisnet http://www.kennisnet.nl
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

source /usr/share/seecr-tools/functions.d/test

set -e
mydir=$(cd $(dirname $0); pwd)
rm -rf tmp build

definePythonVars
$PYTHON setup.py install --root tmp
removeDoNotDistribute tmp
cp -r test tmp/test
find tmp -type f -exec sed -e "
    s,^usrSharePath.*$,usrSharePath='$mydir/tmp/usr/share/meresco-components',;
    " -i {} \;

if [ -z "$@" ]; then
    runtests "alltests.sh"
else
    runtests "$@"
fi


rm -rf tmp build
