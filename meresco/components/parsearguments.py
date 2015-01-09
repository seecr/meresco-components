## begin license ##
# 
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  initiated by Stichting Bibliotheek.nl to provide a new search service
#  for all public libraries in the Netherlands. 
# 
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# 
# This file is part of "NBC+ (Zoekplatform BNL)"
# 
# "NBC+ (Zoekplatform BNL)" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "NBC+ (Zoekplatform BNL)" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "NBC+ (Zoekplatform BNL)"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from optparse import OptionParser, Option

from sys import exit

class ParseArguments(object):
    def __init__(self):
        self._parser = OptionParser()
        self._mandatoryKeys = []
        self.print_help = self._parser.print_help

    def _parse(self, args=None):
        options, arguments = self._parser.parse_args(args)
        for key in self._mandatoryKeys:
            if getattr(options, key, None) == None:
                raise ValueError("Option '%s' is missing." % key)
        return options, arguments

    def addOption(self, *args, **kwargs):
        mandatory = kwargs.pop('mandatory', False)
        if 'help' in kwargs and 'default' in kwargs and '{default}' in kwargs['help']:
            kwargs['help'] = kwargs['help'].format(default=kwargs['default'])
        option = Option(*args, **kwargs)
        if mandatory:
            self._mandatoryKeys.append(option.dest)
        self._parser.add_option(option)

    def parse(self, args=None):
        try:
            return self._parse(args=args)
        except ValueError as e:
            print(('\033[1;31m%s\033[0m' % str(e)))
            self.print_help()
            exit(1)
