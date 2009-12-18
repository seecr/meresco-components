from merescocore.framework import Observable

from cq2utils import DirectoryWatcher
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
    self.do.add(identifier=filename, lxmlNode=<parsed xml>). When the add()
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
        try:
            lxmlNode = parse(open(join(self._inboxDirectory, filename)))
            self.do.add(identifier=filename, lxmlNode=lxmlNode)
        except Exception, e:
            open(join(self._doneDirectory, filename + ".error"), 'w').write(format_exc(limit=7))
        rename(join(self._inboxDirectory, filename), join(self._doneDirectory, filename))