## begin license ##
#
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core".
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase, CallTrace
from meresco.components.messagerewrite import MessageRewrite
from meresco.core import Observable
from weightless.core import be, consume


class MessageRewriteTest(SeecrTestCase):

    def testRewrite(self):
        rewrite = MessageRewrite(fromMessage='this_message', toMessage='to_message')
        observer = CallTrace(emptyGeneratorMethods=['to_message'])
        tree = be((Observable(),
            (rewrite,
                (observer,),
            )
        ))
        consume(tree.all.this_message(aap='noot'))
        self.assertEqual(['to_message'], observer.calledMethodNames())
        self.assertEqual(dict(aap='noot'), observer.calledMethods[0].kwargs)

        observer.calledMethods.reset()
        consume(tree.any.this_message(aap='noot'))
        self.assertEqual(['to_message'], observer.calledMethodNames())
        self.assertEqual(dict(aap='noot'), observer.calledMethods[0].kwargs)

        del observer.emptyGeneratorMethods[:]
        observer.calledMethods.reset()
        tree.call.this_message(aap='noot')
        self.assertEqual(['to_message'], observer.calledMethodNames())
        self.assertEqual(dict(aap='noot'), observer.calledMethods[0].kwargs)

        observer.calledMethods.reset()
        tree.do.this_message(aap='noot')
        self.assertEqual(['to_message'], observer.calledMethodNames())
        self.assertEqual(dict(aap='noot'), observer.calledMethods[0].kwargs)
