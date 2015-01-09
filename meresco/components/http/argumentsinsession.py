## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
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

from meresco.core import Observable

class ArgumentsInSession(Observable):

    def handleRequest(self, session, arguments = {}, *args, **kwargs):
        for k,v in list(arguments.items()):
            if not k in session:
                session[k] = []
            for arg in v:
                if arg[0] in '+-':
                    sign, source = arg[0], arg[1:]
                else:
                    sign = '+'
                    source = repr(arg)
                try:
                    value = eval(source, {'__builtins__': {}})
                except Exception as e:
                    yield 'HTTP/1.0 400 Bad Request\r\n\r\n' + str(e)
                    return
                if sign == '+':
                    if not value in session[k]:
                        session[k].append(value)
                elif sign == '-' and value in session[k]:
                        session[k].remove(value)
        yield self.all.handleRequest(session=session, *args, **kwargs)