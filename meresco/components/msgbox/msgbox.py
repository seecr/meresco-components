## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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

from __future__ import with_statement

from os.path import join, isdir, isfile, basename, abspath
from os import rename, listdir, remove, makedirs, link
from shutil import rmtree
from traceback import format_exc
from sys import stderr

from meresco.core import Observable
from cq2utils import DirectoryWatcher
from weightless import Suspend
from escaping import escapeFilename, unescapeFilename

class Msgbox(Observable):
    """
    Msgbox provides a file based messaging protocol: it receives incoming files and 
    supports a standardized mechanism for sending files.

    Msgbox monitors its inDirectory for files being moved into it. Each moved in file is
    read and passed on to the observers of Msgbox using self.do.add(filepath=filepath). 
    By default a Msgbox writes an acknowledgment (.ack) file to its outDirectory as
    soon as the 'add' call returns. When an exception was raised an error (.error) 
    file is written instead, which contains the full traceback for the error.
    
    To send a file, the Msgbox.add(filename, filedata) method can be used. It writes
    the filedata to the file in a temporary directory and then moves it into the 
    outDirectory. Notice that this allows for another Msgbox instance to receive the
    file.

    An asynchronous Msgbox differs from the default synchronous Msgbox in that it doesn't
    write the .ack file when the self.do.add call returns. Rather, an explicit 
    acknowledgement (or error notification) is expected in the form of a request to 
    send an acknowledgement (or error) file (by way of the previously
    described Msgbox.add method).

    Notes

    The Msgbox intentionally only listens to move events. This avoids reading
    partial files that are still being written to. The move operation is atomic
    and makes sure that the events of putting something into the Msgbox and
    reading it are serialized. NOTE: move files into the Msgbox's inDirectory 
    only from the same file system to keep its atomicity property.

    When the system starts up, the Msgbox does not generate events for files that
    are already in the inDirectory. This avoids uncontrolled bursts.
    Instead, when there are still files in the inDirectory when the system is
    restarted, either move them out and back in again or use the method 
    processInDirectory() to generate events for existing files programmatically.
    """

    def __init__(self, reactor=None, inDirectory='', outDirectory='', asynchronous=False):
        Observable.__init__(self)
        if not isdir(inDirectory):
            raise ValueError("directory %s does not exist" % inDirectory)
        if not isdir(outDirectory):
            raise ValueError("directory %s does not exist" % outDirectory)
        self._inDirectory = inDirectory
        self._outDirectory = outDirectory
        self._tmpDirectory = join(outDirectory, "tmp")
        if isdir(self._tmpDirectory):
            rmtree(self._tmpDirectory)
        makedirs(self._tmpDirectory)
        self._synchronous = not asynchronous
        self._asynchronous = asynchronous
        self._reactor = reactor
        self._suspended = {}

    def observer_init(self):
        self.processInDirectory()
        self._watcher = DirectoryWatcher(self._inDirectory, self._processEvent, MoveInFile=True)
        self._reactor.addReader(self._watcher, self._watcher)

    def processInDirectory(self):
        for filename in listdir(self._inDirectory):
            if (isfile(join(self._inDirectory, filename))):
                self.processFile(filename)

    def _processEvent(self, event):
        self.processFile(event.name)

    def processFile(self, filename):
        filepath = join(self._inDirectory, filename)
        suspend = None
        ackOrError = self._isAckOrError(filename)
        if ackOrError:
            basename, extension = filename.rsplit('.', 1)
            identifier = unescapeFilename(basename)
            suspend = self._suspended.get(identifier, None)
        try:
            if suspend is None:
                identifier = unescapeFilename(filename)
                self.do.add(identifier=identifier, filedata=File(filepath)) # asyncdo !!
                if self._synchronous and not ackOrError:
                    self._ack(filename)
            elif extension == 'error':
                suspend.throw(Exception(open(filepath).read()))
            else:
                suspend.resume()
        except Exception:
            self._logError(format_exc())
            if not ackOrError:
                self._error(filename, format_exc())
        self._forgivingRemove(filepath)

    def _ack(self, filename):
        self._add(filename + ".ack", "")

    def _error(self, filename, errormessage):
        self._add(filename + ".error", errormessage)

    def _isAckOrError(self, filename):
        return filename.endswith('.ack') or filename.endswith('.error')

    def _logError(self, errorMessage):
        stderr.write(errorMessage)
        stderr.flush()

    def add(self, identifier, filedata, **kwargs):
        filename = escapeFilename(identifier)
        self._add(filename, filedata, **kwargs)
        if self._asynchronous:
            suspend = Suspend()
            self._suspended[identifier] = suspend
            yield suspend
            del self._suspended[identifier]
            suspend.getResult()

    def _add(self, filename, filedata, **kwargs):
        """Adds a file to the outDirectory. 
           'filedata' can be one of:
           * a file object
           * a file-like object
           * a string with data
        """
        outFilepath = join(self._outDirectory, filename)
        self._purge(outFilepath)
        tmpFilePath = join(self._tmpDirectory, filename)
        
        try:
            if hasattr(filedata, 'read'):
                link(filedata.name, tmpFilePath)
            else:
                with open(tmpFilePath, 'w') as tmpFile:
                    tmpFile.write(filedata)
            rename(tmpFilePath, outFilepath)
        except:
            self._forgivingRemove(tmpFilePath)
            raise

    def _purge(self, filepath):
        for ext in ('', '.ack', '.error'):
            if isfile(filepath + ext):
                self._forgivingRemove(filepath + ext)

    def _forgivingRemove(self, filepath):
        try:
            remove(filepath)
        except OSError, e:
            if str(e) != "[Errno 2] No such file or directory: '%s'" % filepath:
                raise

class File(object):
    def __init__(self, path):
        self.name = path
        self.__file = None

    def _file(self):
        if self.__file == None:
            self.__file = open(self.name)
        return self.__file

    def __getattr__(self, attr):
        return getattr(self._file(), attr)

    def __iter__(self):
        f = self._file()
        x = f.read(4096)
        while x:
            yield x
            x = f.read(4096)

