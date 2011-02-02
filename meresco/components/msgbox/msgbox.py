# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
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

from sys import exc_info
from os.path import join, isdir, isfile, basename, abspath
from os import rename, listdir, remove, makedirs, link
from shutil import rmtree
from traceback import format_exc, print_exc
from sys import stderr
from random import randint
from tempfile import NamedTemporaryFile

from meresco.core import Observable
from cq2utils import DirectoryWatcher
from weightless import Suspend
from escaping import escapeFilename, unescapeFilename


class Msgbox(Observable):
    """
    Msgbox provides a file based messaging protocol: it receives incoming files and
    supports a standardized mechanism for sending files.

    Msgbox monitors its inDirectory for files being moved into it. Each moved in file is
    read and passed on to the observers of Msgbox using self.do.add(filedata=<File>).
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
        self._waiting = []

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
        needToAck = False
        filepath = join(self._inDirectory, filename)
        suspend = None
        ackOrError = self._isAckOrError(filename)
        if ackOrError:
            basename, extension = filename.rsplit('.', 1)
            identifier = unescapeFilename(basename)
            suspend = self._suspended.pop(identifier, None)
        if not suspend is None:
            if extension == 'error':
                try:
                    raise MsgboxRemoteError(open(filepath).read())
                except:
                    suspend.throw(*exc_info())
            else:
                suspend.resume()
        else:
            identifier = unescapeFilename(filename)
            try:
                self.do.add(identifier=identifier, filedata=File(filepath))
                needToAck = self._synchronous and not ackOrError
            except Exception, e:
                if not self._impliesInputError(e):
                    print_exc()
                if not ackOrError:
                    self._error(filename, format_exc())
        remove(filepath)
        if needToAck:
            self._ack(filename)
        elif ackOrError:
            for suspendedidentifier, suspend in self._waiting:
                if suspendedidentifier == identifier:
                    self._waiting.remove((suspendedidentifier, suspend))
                    suspend.resume()
                    break

    def add(self, identifier, filedata, **kwargs):
        filename = escapeFilename(identifier)
        outFilePath = join(self._outDirectory, filename)
        if hasattr(filedata, 'read'):
            tmpFilePath = self._tempFileName()
            link(filedata.name, tmpFilePath)
        else:
            tmpFilePath = self._writeTempFile(filedata)
        if self._asynchronous:
            suspend = Suspend()
            while isfile(outFilePath) or identifier in self._suspended:
                self._waiting.append((identifier, suspend))
                yield suspend
                suspend.getResult()
            assert identifier not in self._suspended
            self._suspended[identifier] = suspend
            self._moveOrDitch(tmpFilePath, outFilePath)
            yield suspend
            suspend.getResult()
        else:
            self._moveOrDitch(tmpFilePath, outFilePath)


    def _isAckOrError(self, filename):
        return filename.endswith('.ack') or filename.endswith('.error')

    def _ack(self, filename):
        self._atomicWrite(filename + ".ack", "")

    def _error(self, filename, errormessage):
        self._atomicWrite(filename + ".error", errormessage)

    def _atomicWrite(self, name, data):
        path = self._writeTempFile(data)
        self._moveOrDitch(path, join(self._outDirectory, name))

    def _writeTempFile(self, data):
        tmpFilePath = self._tempFileName()
        with open(tmpFilePath, 'w') as tmpFile:
            tmpFile.write(data)
        return tmpFilePath

    def _tempFileName(self):
        return join(self._tmpDirectory, str(randint(1, 2**48)))

    def _moveOrDitch(self, src, dst):
        try:
            rename(src, dst)
        finally:
            if isfile(src):
                remove(src)

    def _impliesInputError(self, e):
        # Input (Java) errors, like invalid RDF, must be ValueErrors.
        return isinstance(e, ValueError) or \
               (isinstance(e, IOError) and e.errno == 2)  # No such file or directory


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


class MsgboxRemoteError(RuntimeError):
    pass

