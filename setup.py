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

from distutils.core import setup
from distutils.extension import Extension

setup(
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
        Extension("merescocomponents.facetindex._facetindex", [
                      'merescocomponents/facetindex/zipper.c',
                      'merescocomponents/facetindex/_docsetlist.cpp',
                      'merescocomponents/facetindex/_docset.cpp',
                      'merescocomponents/facetindex/_integerlist.cpp',
                      'merescocomponents/facetindex/fwpool.c',
                      'merescocomponents/facetindex/trie_c.cpp',
                      'merescocomponents/facetindex/_triedict.cpp',
                      'merescocomponents/facetindex/_stringpool.cpp',
                  ],
                  extra_compile_args = [
                      '-I/usr/include/glib-2.0',
                      '-I/usr/lib/glib-2.0/include',
                  ],
                  extra_link_args = [
                      '/usr/lib/python2.5/site-packages/_PyLucene.so'
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
