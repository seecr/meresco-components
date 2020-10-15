#!/usr/bin/env python3
# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from os import system                            #DO_NOT_DISTRIBUTE
system('find .. -name "*.pyc" | xargs rm -f')    #DO_NOT_DISTRIBUTE
from seecrdeps import includeParentAndDeps       #DO_NOT_DISTRIBUTE
includeParentAndDeps(__file__, scanForDeps=True) #DO_NOT_DISTRIBUTE

from meresco.core import Observable
from meresco.components import ParseArguments
from meresco.components.json import JsonDict, JsonList
from meresco.components.http import ObservableHttpServer, BasicHttpHandler

from weightless.io import Reactor
from weightless.core import compose, be

class RequestEcho(object):
    def handleRequest(self, *args, **kwargs):
        yield "HTTP/1.0 200 OK\r\n"
        yield "\r\n"
        yield JsonList(args).pretty_print()
        yield JsonDict(kwargs).pretty_print()

def dna(reactor, port, **kwargs):
    return (Observable(),
        (ObservableHttpServer(reactor, bindAddress='0.0.0.0', port=port),
            (BasicHttpHandler(),
                (RequestEcho(), )
            )
        )
    )

if __name__ == '__main__':
    parser = ParseArguments()
    parser.addOption("", '--port', type='int', mandatory=False, default=6060)
    options, arguments = parser.parse()

    reactor = Reactor()
    server = be(dna(reactor=reactor, **vars(options)))
    list(compose(server.once.observer_init()))
    reactor.loop()

