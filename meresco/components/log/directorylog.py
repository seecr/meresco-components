# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2006-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2006-2012, 2014, 2016, 2026 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012-2016, 2018, 2026 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from time import strftime, gmtime, time
from .logline import LogLine
import pathlib
import gzip

NR_OF_FILES_KEPT = 14

GZ_EXTENSION = ".gz"


class DirectoryLogRotate(object):
    def __init__(self, logdir, extension="-query.log", nrOfFilesKept=NR_OF_FILES_KEPT):
        self._previousLog = None
        self._logpath = pathlib.Path(logdir)
        if not self._logpath.is_dir():
            self._logpath.mkdir()
        self._filenameExtension = extension
        self._nrOfFilesKept = nrOfFilesKept
        self._now = time
        self._cleanupLogs()

    def setNrOfFilesKept(self, value):
        if value > 0:
            self._nrOfFilesKept = value

    def _filename(self, timestamp):
        date = strftime("%Y-%m-%d", gmtime(timestamp))
        return self._logpath.joinpath(f"{date}{self._filenameExtension}")

    def _logfiles(self):
        return sorted(
            f.name
            for f in self._logpath.iterdir()
            if f.name.endswith(self._filenameExtension)
            or f.name.endswith(self._filenameExtension + GZ_EXTENSION)
        )

    def logExists(self, logName):
        return (
            self._logpath.joinpath(logName).is_file()
            or self._logpath.joinpath(logName + GZ_EXTENSION).is_file()
        )

    def listlogs(self):
        return [
            name[: -len(GZ_EXTENSION)] if name.endswith(GZ_EXTENSION) else name
            for name in self._logfiles()
        ]

    def getlog(self, logName):
        logFilename = self._logpath.joinpath(logName)
        if logFilename.is_file():
            with logFilename.open() as f:
                for line in f:
                    yield line
        else:
            logFilenameGz = logFilename.with_suffix(logFilename.suffix + GZ_EXTENSION)
            with gzip.open(logFilenameGz, "rt") as f:
                for line in f:
                    yield line

    def write(self, line, **kwargs):
        timestamp = kwargs.pop("timestamp", self._now())
        logFilename = self._filename(timestamp)

        if logFilename != self._previousLog:
            self._cleanupLogs()
            if logFilename.with_suffix(logFilename.suffix + GZ_EXTENSION).is_file():
                raise ValueError(f"Can't write historical timestamps")
            self._previousLog = logFilename

        with logFilename.open("a") as f:
            f.write(line)

    def flush(self):
        pass

    def _cleanupLogs(self):
        logs = self._logfiles()
        while len(logs) >= self._nrOfFilesKept:
            self._logpath.joinpath(logs[0]).unlink()
            logs = self._logfiles()
        for log in logs[:-1]:
            if log.endswith(GZ_EXTENSION):
                continue
            with self._logpath.joinpath(log).open() as f:
                with gzip.open(self._logpath.joinpath(log + GZ_EXTENSION), "wt") as gz:
                    for line in f:
                        gz.write(line)
            self._logpath.joinpath(log).unlink()


class DirectoryLog(DirectoryLogRotate):
    def __init__(self, *args, **kwargs):
        self._logline = kwargs.pop("logline", LogLine.createDefault())
        DirectoryLogRotate.__init__(self, *args, **kwargs)

    def log(self, **kwargs):
        self.write(self._logline(kwargs), timestamp=kwargs["timestamp"])
