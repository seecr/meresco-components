## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from seecr.test import SeecrTestCase
from os.path import join
from meresco.components.log.utils import LogParse

class LogUtilsTest(SeecrTestCase):

    def testParseLines(self):
        with open(join(self.tempdir, 'f'), 'w') as f:
            f.write('''2015-10-08T00:00:04Z 127.0.0.1 0.1K 0.1s 1hits /path key=value
2015-10-08T00:00:04Z 127.0.0.2 0.2K 0.2s 2hits /path key=value
2015-10-08T00:00:04Z 127.0.0.3 0.3K 0.3s 3hits /path
''')
        result = list(LogParse.parse(join(self.tempdir, 'f')).lines())
        self.assertEquals(3, len(result))
        self.assertEquals(('2015-10-08T00:00:04Z', '127.0.0.3', '0.3K', '0.3s', '3hits', '/path', ''), result[-1])
        self.assertEquals(dict(timestamp='2015-10-08T00:00:04Z', ipaddress='127.0.0.2', size='0.2K', duration='0.2s', hits='2hits', path='/path', arguments='key=value'), dict(vars(result[1])))
        self.assertEquals('1hits', result[0].hits)

    def testParseCustomLines(self):
        with open(join(self.tempdir, 'f'), 'w') as f:
            f.write('''1hits /path key=value
2hits /path key=value
3hits /path
''')
        result = list(LogParse.parse(open(join(self.tempdir, 'f')), parts=['a','b','c','d','e']).lines())
        self.assertEquals(('3hits', '/path', '', '', ''), result[-1])
        self.assertEquals(dict(a='2hits', b='/path', c='key=value', d='', e=''), dict(vars(result[1])))
        self.assertEquals('1hits', result[0].a)