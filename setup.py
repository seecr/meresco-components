
from distutils.core import setup
from distutils.extension import Extension

setup(
    name = 'merescocomponents',
    packages = ['merescocomponents'],
    ext_modules = [
        Extension("merescocomponents.facetindex._facetindex", [
                'merescocomponents/facetindex/zipper.c',
                'merescocomponents/facetindex/_docsetlist.cpp',
                'merescocomponents/facetindex/_docset.cpp',
                'merescocomponents/facetindex/fwpool.c',
                'merescocomponents/facetindex/fwstring.c',
                'merescocomponents/facetindex/trie_c.cpp',
                ],
        	extra_compile_args = ['-I/usr/include/glib-2.0', '-I/usr/lib/glib-2.0/include'],
            extra_link_args = ['/usr/lib/python2.5/site-packages/_PyLucene.so']
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
