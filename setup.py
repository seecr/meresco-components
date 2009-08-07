# -*- coding: utf-8 -*-
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

import sys
import os
import string
from types import ListType, TupleType
from distutils.core import setup
from distutils.extension import Extension
from distutils.command.build_ext import build_ext
from distutils.command.clean import clean
from distutils.dep_util import newer_group
from distutils.core import setup
from distutils import log


CLASSPATH = "merescocomponents/facetindex/lucene-core-2.2.0.jar"
class gcj_build_ext(build_ext):
    """Adds GCJ compilation of Java sources into object files that get linked into the specified extension."""

    def build_extension(self, ext):
        # largely copied from distutils/command/build_ext.py, which lacks desired hooks
        sources = ext.sources
        if sources is None or type(sources) not in (ListType, TupleType):
            raise DistutilsSetupError, \
                  ("in 'ext_modules' option (extension '%s'), " +
                   "'sources' must be present and must be " +
                   "a list of source filenames") % ext.name

        fullname = self.get_ext_fullname(ext.name)
        if self.inplace:
            # ignore build-lib -- put the compiled extension into
            # the source tree along with pure Python modules

            modpath = string.split(fullname, '.')
            package = string.join(modpath[0:-1], '.')
            base = modpath[-1]

            build_py = self.get_finalized_command('build_py')
            package_dir = build_py.get_package_dir(package)
            ext_filename = os.path.join(package_dir,
                                        self.get_ext_filename(base))
        else:
            ext_filename = os.path.join(self.build_lib,
                                        self.get_ext_filename(fullname))
        depends = sources + ext.depends
        if not (self.force or newer_group(depends, ext_filename, 'newer')):
            log.debug("skipping '%s' extension (up-to-date)", ext.name)
            return

        jsources = [src for src in sources if src.endswith('.java')]
        jofiles = [self.oFileForJava(src, output_dir=self.build_temp) for src in jsources]
        depends = jsources + ext.depends
        compiledJava = False
        if self.force or newer_group(depends, ext_filename, 'newer'):
            log.info("building '%s' extension, compiling Java", ext.name)
            self.compileJava(jsources,
                             output_dir=self.build_temp)
            compiledJava = True
            self.force = True

        ext.extra_objects = (ext.extra_objects if hasattr(ext, 'extra_objects') else []) + jofiles
        ext.sources = [src for src in ext.sources if not src.endswith('.java')]
        build_ext.build_extension(self, ext)

        if compiledJava:
            # XXX -- this is a Vile HACK!
            #
            # The setup.py script for Python on Unix needs to be able to
            # get this list so it can perform all the clean up needed to
            # avoid keeping object files around when cleaning out a failed
            # build of an extension module.  Since Distutils does not
            # track dependencies, we have to get rid of intermediates to
            # ensure all the intermediates will be properly re-built.
            #
            self._built_objects = jofiles + (self._built_objects or [])

    def oFileForJava(self, source, output_dir):
        return "%s/%s.o" % (output_dir, os.path.splitext(source)[0])

    def compileJava(self, sources, output_dir):
        for s in sources:
            oFile = self.oFileForJava(s, output_dir)
            try:
                os.makedirs(os.path.dirname(oFile))
            except OSError:
                pass
            cl = "CLASSPATH=%s gcj -fPIC -c %s -o %s" % (CLASSPATH, s, oFile)
            log.info(cl)
            rv = os.system(cl)
            if rv != 0:
                print "Build failed, exiting."
                sys.exit(rv)


setup(
    cmdclass={
              'build_ext': gcj_build_ext,
             },
    name = 'merescocomponents',
    packages = [
        'merescocomponents',
        'merescocomponents.facetindex',
        'merescocomponents.facetindex.tools',
        'merescocomponents.oai',
        'merescocomponents.web',
        'merescocomponents.examples',
        'merescocomponents.examples.dna',
    ],
    ext_modules = [
        Extension("merescocomponents.facetindex._facetindex",
                  [
                      'merescocomponents/facetindex/zipper.c',
                      'merescocomponents/facetindex/_docsetlist.cpp',
                      'merescocomponents/facetindex/_docset.cpp',
                      'merescocomponents/facetindex/_integerlist.cpp',
                      'merescocomponents/facetindex/fwpool.c',
                      'merescocomponents/facetindex/trie_c.cpp',
                      'merescocomponents/facetindex/_triedict.cpp',
                      'merescocomponents/facetindex/_stringpool.cpp',
                      'merescocomponents/facetindex/MerescoStandardAnalyzer.java',
                  ],
                  extra_compile_args = [
                      '-I/usr/include/glib-2.0',
                      '-I/usr/lib/glib-2.0/include',
                  ],
                  extra_link_args = [
                      '-llucene-core',
                  ],
        )
    ],
    version = '%VERSION%',
    url = 'http://www.cq2.nl',
    author = 'Seek You Too',
    author_email = 'info@cq2.nl',
    description = 'Meresco Components are components to build searchengines, repositories and archives, based on Meresco Core.',
    long_description = 'Meresco Components are components to build searchengines, repositories and archives, based on Meresco Core.',
    license = 'GPL',
    platforms='all',
)
