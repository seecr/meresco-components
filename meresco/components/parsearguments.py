## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2011-2012, 2015-2016, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2020 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 SURF https://www.surf.nl
# Copyright (C) 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from optparse import OptionParser, Option

from sys import exit
from warnings import warn

class ParseArguments(object):
    def __init__(self, usage=None, description=None, epilog=None):
        warn("Please use python default module argparse.", DeprecationWarning)
        optKwargs = {}
        if description:
            optKwargs['description'] = description
        if epilog:
            optKwargs['epilog'] = epilog
        if usage:
            optKwargs['usage'] = usage
        self._parser = OptionParser(**optKwargs)
        self._mandatoryKeys = []
        self.print_help = self._parser.print_help
        self.error = self._parser.error

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
        if option.metavar is None:
            option.metavar = '<{0}>'.format(option.type) if kwargs.get('default') is None else repr(option.default)
        if mandatory:
            self._mandatoryKeys.append(option.dest)
        self._parser.add_option(option)

    def parse(self, args=None):
        try:
            return self._parse(args=args)
        except ValueError as e:
            print('\033[1;31m%s\033[0m' % str(e))
            self.print_help()
            exit(1)
