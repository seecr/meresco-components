# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from os.path import isdir
from subprocess import Popen, PIPE

from meresco.components.facetindex.merescolucene import FSDirectory, IndexReader, Directory


def unlock(path):
    """
    Unlock the directory specified by path.
    This is a manual operation, when locking somehow has gone wrong.
    """
    _assertNoFilesOpenInPath(path)
    IndexReader.unlock(FSDirectory.getDirectory(path, False) % Directory)

def _assertNoFilesOpenInPath(path, lsofFunc=None):
    lsofFunc = lsofFunc if lsofFunc else _lsof
    if isdir(path):
        cmdline, out, err, exitcode = lsofFunc(path)
        if err:
            raise Exception("'%s' failed:\n%s" % (cmdline, err))
        if out:
            raise Exception("Refusing to remove lock because index is in use by PIDs: %s" % out.strip())

def _lsof(path):
    cmdline = "lsof -t +D %s" % path # -t output only pid's, +D scan directory recursively
    process = Popen(cmdline.split(" "), stdout=PIPE, stderr=PIPE)
    (out, err) = process.communicate()
    return cmdline, out, err, process.poll()
