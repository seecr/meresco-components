## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2008-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2008-2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.core import Observable
from weightless.core import compose

from meresco.components import DirectoryWatcher
from lxml.etree import parse

from os.path import join, isdir
from os import rename, listdir
from traceback import format_exc

class InboxException(Exception):
    pass

class Inbox(Observable):
    """
    Inbox monitors a directory for files XML files being moved into it.  Each
    file moved into the directory is assumed to be in XML format.  It is read,
    parsed (using lxml) and passed on to the observers of Inbox using
    self.all.add(identifier=filename, lxmlNode=<parsed xml>). When the add()
    calls succeeds, the file is moved to another directory.

    Parameters

    Both the inbox directory and the done directory are taken as parameters from
    the constructor (__init__).  It is strongly recommended to put both
    directories on the same file system, so the move is atomic and does not
    incur data copying.

    Errors

    When an error occured, the file causing the error is also moved to the done
    directory, but an .error file is written next to it.  This file contains
    a complete stacktrace of the error.

    Notes

    The Inbox intentionally only listens to move events.  This avoids reading
    partial files that are still being written to.  The move operation is atomic
    and makes sure that the events of putting something into the inbox and
    reading it are serialized.  NOTE: move files into the inbox only from the
    same file system to keep it atomicity property.

    When the system starts up, the Inbox does not generate events for files that
    are already in the inbox directory.  This avoids uncontrolled bursts.
    Instead, when there are still files in the inbox when the system is
    restarted, either move them out and than back into the directory.
    Alternatively, one could use the method processInboxDirectory() to generate
    events for existing files programmatically.
    """
    def __init__(self, reactor=None, inboxDirectory='', doneDirectory=''):
        Observable.__init__(self)

        if not isdir(inboxDirectory):
            raise InboxException("directory %s does not exist" % inboxDirectory)

        if not isdir(doneDirectory):
            raise InboxException("directory %s does not exist" % doneDirectory)

        self._inboxDirectory = inboxDirectory
        self._doneDirectory = doneDirectory
        self._watcher = DirectoryWatcher(self._inboxDirectory, self._processEvent, MoveInFile=True)
        reactor.addReader(self._watcher, self._watcher)

    def processInboxDirectory(self):
        for filename in listdir(self._inboxDirectory):
            self.processFile(filename)

    def _processEvent(self, event):
        self.processFile(event.name)

    def processFile(self, filename):
        errorFilename = join(self._doneDirectory, filename + ".error")
        try:
            lxmlNode = parse(open(join(self._inboxDirectory, filename)))
            composed = compose(self.all.add(identifier=filename, lxmlNode=lxmlNode))
            try:
                while True:
                    composed.next()
            except StopIteration, e:
                pass
        except Exception, e:
            open(errorFilename, 'w').write(format_exc())

        try:
            rename(join(self._inboxDirectory, filename), join(self._doneDirectory, filename))
        except Exception, e:
            open(errorFilename, 'a').write(format_exc())
