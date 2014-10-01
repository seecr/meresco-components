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

from unittest import TestCase
from meresco.components import ParseArguments
from seecr.test.io import stdout_replaced

class ParseArgumentsTest(TestCase):
    def testMandatoryKey(self):
        parser = ParseArguments()
        parser.addOption('', '--name', help='Naam', mandatory=True)
        parser.addOption('', '--port', help='Port', type='int', mandatory=True)
        argv = ['script', '--name', 'TestServer', '--port', '1234']
        options, arguments = parser.parse(argv)
        self.assertEquals(1234, options.port)
        self.assertEquals('TestServer', options.name)
        argv = ['script', '--port', '1234']
        self.assertRaises(ValueError, parser._parse, argv)

    def testAdditionalOptions_optional(self):
        argv = ['script', '--name', 'TestServer']
        parser = ParseArguments()
        parser.addOption('', '--name', help='Naam', mandatory=True)
        parser.addOption('', '--port', help='Port', type='int')
        parser.addOption('', '--withDefault', help='Default', default="default", type='str')
        options, arguments = parser.parse(argv)
        self.assertEquals('TestServer', options.name)
        self.assertEquals(None, options.port)
        self.assertEquals('default', options.withDefault)

    def testDefaultValueInHelp(self):
        parser = ParseArguments()
        parser.addOption('', '--option', help='Option with a default value of {default}', default=42)

        with stdout_replaced() as out:
            parser.print_help()
            self.assertTrue("Option with a default value of 42" in out.getvalue(), out.getvalue())

