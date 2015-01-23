## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2011-2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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
        self.assertEqual(1234, options.port)
        self.assertEqual('TestServer', options.name)
        argv = ['script', '--port', '1234']
        self.assertRaises(ValueError, parser._parse, argv)

    def testAdditionalOptions_optional(self):
        argv = ['script', '--name', 'TestServer']
        parser = ParseArguments()
        parser.addOption('', '--name', help='Naam', mandatory=True)
        parser.addOption('', '--port', help='Port', type='int')
        parser.addOption('', '--withDefault', help='Default', default="default", type='str')
        options, arguments = parser.parse(argv)
        self.assertEqual('TestServer', options.name)
        self.assertEqual(None, options.port)
        self.assertEqual('default', options.withDefault)

    def testDefaultValueInHelp(self):
        parser = ParseArguments()
        parser.addOption('', '--option', help='Option with a default value of {default}', default=42)

        with stdout_replaced() as out:
            parser.print_help()
            self.assertTrue("Option with a default value of 42" in out.getvalue(), out.getvalue())

    def testMetaVars(self):
        parser = ParseArguments()
        parser.addOption('', '--option')
        parser.addOption('', '--defaultValue', default='default')
        parser.addOption('', '--port', help='Port', type='int')
        parser.addOption('', '--otherPort', help='Port', type='int', default=10000)
        parser.addOption('', '--quiet', action='store_false', default=True, dest='verbose')
        with stdout_replaced() as out:
            parser.print_help()
            self.assertTrue("--option=<string>" in out.getvalue(), out.getvalue())
            self.assertTrue("--defaultValue='default'" in out.getvalue(), out.getvalue())
            self.assertTrue("--port=<int>" in out.getvalue(), out.getvalue())
            self.assertTrue("--otherPort=10000" in out.getvalue(), out.getvalue())

