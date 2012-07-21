# neubot/utils_path.py

#
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

''' Path management utils '''

import collections
import os.path
import sys

def depth_visit(prefix, components, visit):
    ''' Visit the subtree prefix/components[0]/components[1]... '''
    #
    # Append() guarantees that the result is always below prefix,
    # so the result of this function is below prefix as well.
    # It is not an error to pass a component that contains one or
    # more path separators, except that subcomponents are not visited
    # in that case.
    # The boolean second argument to visit is to distinguish between
    # leaf and ordinary nodes.
    # This function is more strict than needed and generates an
    # error for input like '/var/www', ['a/b/c', '../d'], but we
    # don't care because that case doesn't happen in Neubot.
    #
    components = collections.deque(components)
    while components:
        prefix = append(prefix, components.popleft())
        visit(prefix, not components)
    return prefix

def append(prefix, path):
    ''' Safely append path to prefix '''
    #
    # To avoid surprises with unicode characters, we ensure that we
    # pass normalize() 'ascii'-only path and prefix.
    # The return value of normalize() is either an absolute path or
    # a relative path, possibly starting with one or more up-level
    # references, i.e. '../' or '..\\'.
    # To guarantee that the join() result is always below prefix we
    # raise an error if path contains any reference to the upper
    # level.  Moreover, prefix must be absolute because it is a bit
    # confusing to have relative prefixes.
    # Then there's normalize() step is to collapse eventual consecutive
    # slashes added by the join(), which happens when path isabs(),
    # and, finally, just for correctness we force the result to be ASCII,
    # since in some cases normalize() returns a unicode object.
    #
    return                     must_be_ascii(
                                normalize(
                                   join(
                 must_be_absolute(
           normalize(
   must_be_ascii(prefix))),
                                          must_not_be_upref(
                                               normalize(
                                                   must_be_ascii(path))))))

#
# Define constant to make must_be_ascii() portable, we use
# the naming convention of python3 because it's much easier
# to understand: you go from bytes to str with decode(),
# from str to bytes with encode().
#
if sys.version_info[0] < 3:
    PY3_STRING = unicode
else:
    PY3_STRING = str

def must_be_ascii(string):
    ''' Raises an exception if string contains non ASCII characters,
        where string may be either 'bytes' or 'str' and the return value
        is always a 'str'. '''
    #
    # When the input is already a 'str' we need an extra decode()
    # step to convert back 'bytes' to 'str'.
    #
    if isinstance(string, PY3_STRING):
        return string.encode('ascii').decode('ascii')
    else:
        return string.decode('ascii')

def normalize(string):
    ''' Normalize a pathname '''
    #
    # Collapses redundant path seps and up-level references, converts
    # forward slashes to back slashes on Windows.
    # The result is either an absolute path without uplevel references
    # (upref), a relative path w/o uprefs, or a relative path w/ one
    # or more uprefs at the beginning, an no further uprefs after the
    # first dir or file name.
    #
    return os.path.normpath(string)

#
# must_be_absolute() and must_not_be_upref() both run after
# normalize(), so they use os.sep as separator.
#

def must_be_absolute(string):
    ''' Raises an exception if a path is not absolute '''
    if not os.path.isabs(string):
        raise ValueError('utils_path: relative path')
    return string

UPREF = '..%s' % os.sep

def must_not_be_upref(string):
    ''' Raises an exception if path is an up-level reference '''
    if string.startswith(UPREF):
        raise ValueError('utils_path: up-level reference path')
    else:
        return string

def join(left, right):
    ''' Join two paths '''
    return os.sep.join([left, right])
