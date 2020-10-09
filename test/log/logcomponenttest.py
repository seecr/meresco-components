# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase, CallTrace
from seecr.test.io import stdout_replaced

from weightless.core import be, retval

from meresco.core import Observable

from meresco.components.log import LogComponent


class LogComponentTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.observer = CallTrace('observer')
        self.top = be((Observable(),
            (LogComponent('x'),
                (self.observer,),
             )
        ))

    def testLogCall(self):
        args, kwargs = ('a',), {'b': 'c'}
        with stdout_replaced() as out:
            self.top.call.aMessage('a', b='c')
            self.assertCall('aMessage', args, kwargs, out)

        with stdout_replaced() as out:
            self.top.call.aMessage(*args, **kwargs)
            self.assertCall('aMessage', args, kwargs, out)

        # "message" is the only keyword-argument that cannot be handled by anything implementing *_unknown.
        try:
            self.top.call.aMessage(message='m')
        except TypeError as e:
            self.assertTrue("got multiple values for argument 'message'" in str(e), str(e))

        # ... and "method" does work (broken in previous version).
        with stdout_replaced() as out:
            self.top.call.notherMessage(method='f')
            self.assertCall('notherMessage', tuple(), {'method': 'f'}, out)

        # retval roundtrip
        self.observer.methods['f'] = lambda: 42
        with stdout_replaced() as out:
            result = self.top.call.f()
            self.assertEqual(42, result)
            self.assertCall('f', tuple(), {}, out)

    def assertCall(self, message, args, kwargs, out):
        self.assertEqual([message], self.observer.calledMethodNames())
        calledMethod = self.observer.calledMethods[0]
        self.assertEqual((args, kwargs), (calledMethod.args, calledMethod.kwargs))
        self.assertEqual(msg(message, args, kwargs), out.getvalue())
        self.observer.calledMethods.reset()


def msg(message, args, kwargs):
    # LogComponent is used for debugging - so exact message not that important here.
    return "[x] %(message)s(*%(args)s, **%(kwargs)s)\n" % locals()
