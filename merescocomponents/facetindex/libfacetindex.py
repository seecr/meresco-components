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
from ctypes import cdll, c_int, c_uint, c_uint32
from os.path import join, abspath, dirname

print "loading libFacetIndex"
libFacetIndex = cdll.LoadLibrary(join(abspath(dirname(__file__)), '_facetindex.so'))
print "libFacetIndex loaded"

class MangleException(Exception): pass

def mangle(names, argtypes):
    """http://www.codesourcery.com/public/cxx-abi/abi.html#mangling"""
    mangled_name = '_Z'
    types = {
        c_uint32:   'j',
        c_uint:     'j',
        c_int:      'i',
        None:       'v',
    }
    mangled_name += 'N'
    for name in names:
        mangled_name += str(len(name)) + name
    mangled_name += 'E'
    for argtype in argtypes:
        try:
            builtin_type = types[argtype]
        except KeyError:
            raise MangleException('Mangling %s not supported yet.' % argtype)
        mangled_name += types[argtype]
    return mangled_name

class c_method(object):
    """ decorator for methods implemented in C
    For a method MyClass.myMethod, it looks for MyClass_myMethod in the C-extension.
    The class MyClass must have an attribute c_type reflecting the class in C.
    Objects of MyClass must have the attribute _as_parameter_ set to a value of c_type
    Classmethod decorators must be placed above the c_method decorator.
    Type information is taken as parameters: c_method(argtypes: tuple, restype: object) and specified using ctypes types such as c_int etc.
    The Python method is not called.  Use c_wrapper if you want it to be called.

    class MYCLASS(Structure):
        _fields_ = [("type", c_int, 2),
                    ("ptr", c_int, 30)]

    class MyClass(object):
        c_type = MYCLASS

        def __init__(self, c_obj):
            self._as_parameter_ = c_obj

        @classmethod
        @c_wrapper(argtypes=(), restype=MYCLASS)
        def create(clazz, c_funct):
            c_obj = c_funct()
            return DocSet(c_obj)

        @c_method(argtypes=(c_uint32,), restype=c_int)
        def contains(self, size):
            pass
    """

    def __init__(self, argtypes, restype):
        self._lib = libFacetIndex
        self._argtypes = argtypes
        self._restype = restype

    def __call__(self, py_funct):
        def helper(this, *args, **kwargs):
            if not hasattr(py_funct, 'c_funct'):
                clazz = this if type(this) == type else type(this)
                try:
                    c_name = mangle((clazz.__name__, py_funct.func_name), self._argtypes)
                    c_funct = getattr(self._lib, c_name)
                except (MangleException, AttributeError):
                    c_name = clazz.__name__ + '_' + py_funct.func_name
                    c_funct = getattr(self._lib, c_name)
                if type(this) == type:
                    c_funct.argtypes = self._argtypes
                else:
                    c_funct.argtypes = (this.c_type,) + self._argtypes
                c_funct.restype = self._restype
                py_funct.c_funct = c_funct
            if type(this) != type and hasattr(this, 'from_param') and py_funct.func_name != 'from_param':
                m = type(this).from_param
                this = m(this._as_parameter_)
            return self._doCall(this, py_funct, py_funct.c_funct, args, kwargs)
        helper.func_name = py_funct.func_name + '_helper'
        return helper

    def _doCall(self, this, py_funct, c_funct, args, kwargs):
        if type(this) == type:
            return c_funct(*args, **kwargs)
        return c_funct(this, *args, **kwargs)


class c_wrapper(c_method):

    def _doCall(self, this, py_funct, c_func, args, kwargs):
        return py_funct(this, c_func, *args, **kwargs)
