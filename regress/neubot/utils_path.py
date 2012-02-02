#!/usr/bin/env python

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

''' Regression test for neubot/utils_path.py '''

import unittest
import os
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import utils_path

class TestDepthVisit(unittest.TestCase):

    ''' Make sure depth_visit() works as expected '''

    #
    # This test case wants to garner confidence that:
    #
    # 1. visit() is not invoked when components is empty;
    #
    # 2. depth_visit() bails out w/ nonabsolute prefix;
    #
    # 3. depth_visit() bails out w/ nonascii prefix;
    #
    # 4. depth_visit() bails out w/ nonascii component;
    #
    # 5. depth_visit() bails out w/ upref components;
    #
    # 6. depth_visit() is more restrictive than needed, and
    #    rejects some paths that are below prefix due to the
    #    way it is implemented;
    #
    # 7. depth_visit() visits nodes in the expected order;
    #
    # 8. depth_visit() correctly flags the leaf node.
    #

    def test__1(self):
        ''' Make sure depth_visit() works OK w/ empty components '''

        visit_called = [0]
        def on_visit_called(*args):
            ''' Just an helper function '''
            visit_called[0] += 1

        utils_path.depth_visit('/foo', [], on_visit_called)

        self.assertFalse(visit_called[0])

    def test__2(self):
        ''' Make sure depth_visit() fails w/ nonabsolute prefix '''
        self.assertRaises(ValueError, utils_path.depth_visit,
          'foo', ['bar', 'baz'], lambda *args: None)

    def test__3(self):
        ''' Make sure depth_visit() fails w/ nonascii prefix '''
        self.assertRaises(UnicodeError, utils_path.depth_visit,
          '/foo\xc3\xa8', ['bar', 'baz'], lambda *args: None)

    def test__4(self):
        ''' Make sure depth_visit() fails w/ nonascii component '''
        self.assertRaises(UnicodeError, utils_path.depth_visit,
          '/foo', ['bar', 'baz\xc3\xa8'], lambda *args: None)

    def test__5(self):
        ''' Make sure depth_visit() fails w/ upref components '''
        self.assertRaises(ValueError, utils_path.depth_visit,
          '/foo', ['../../baz/xo'], lambda *args: None)

    def test__6(self):
        ''' Verify that depth_visit() is more restrictive than needed '''
        self.assertRaises(ValueError, utils_path.depth_visit,
          '/foo', ['/bar/bar', '../baz/xo'], lambda *args: None)

    def test__7(self):
        ''' Make sure depth_visit() visits in the expected order '''

        # The result depends on the OS
        expected = [
                    os.sep.join(['', 'foo', 'bar']),
                    os.sep.join(['', 'foo', 'bar', 'baz']),
                    os.sep.join(['', 'foo', 'bar', 'baz', 'barbar',]),
                    os.sep.join(['', 'foo', 'bar', 'baz', 'barbar', 'bazbaz']),
                   ]

        visit_order = []
        def on_visit_called(*args):
            ''' Just an helper function '''
            visit_order.append(args[0])

        components = ['bar', 'baz', 'barbar', 'bazbaz']
        utils_path.depth_visit('/foo', components, on_visit_called)
        self.assertEquals(visit_order, expected)

    def test__8(self):
        ''' Make sure depth_visit() correctly flags the leaf node '''

        # The result depends on the OS
        expected = os.sep.join(['', 'foo', 'bar', 'baz',
                                'barbar', 'bazbaz'])

        failure = [False]
        def on_visit_called(*args):
            ''' Just an helper function '''
            if args[1] and args[0] != expected:
                failure[0] = True

        components = ['bar', 'baz', 'barbar', 'bazbaz']
        utils_path.depth_visit('/foo', components, on_visit_called)
        self.assertFalse(failure[0])

class TestAppend(unittest.TestCase):

    ''' Make sure append() works as expected '''

    #
    # This test case wants to gain confidence that the following
    # statements are true:
    #
    # 1. that append() bails out when prefix is nonascii;
    #
    # 2. that append() bails out when path is nonascii;
    #
    # 3. that append() bails out when prefix is nonabsolute;
    #
    # 4. that append() bails out when prefix is up-ref;
    #
    # 5. that append() squeezes after-join() multiple slashes.
    #

    def test__1(self):
        ''' Test append() bails out when prefix is nonascii '''
        self.assertRaises(UnicodeError, utils_path.append,
                          '/cio\xc3\xa8', '/foobar')

    def test__2(self):
        ''' Test append() bails out when path is nonascii '''
        self.assertRaises(UnicodeError, utils_path.append,
                          '/foobar', '/cio\xc3\xa8')

    def test__3(self):
        ''' Test append() bails out when prefix is nonabsolute '''
        self.assertRaises(ValueError, utils_path.append,
                          'foobar', '/foobaz')

    def test__4(self):
        ''' Test append() bails out when path is nonabsolute and upref '''
        self.assertRaises(ValueError, utils_path.append,
                          '/foobar', '../foobaz')

    def test__5(self):
        ''' Test append() squeezes after-join() multiple slashes '''
        self.assertEqual(utils_path.append('/foo', '/bar'), '/foo/bar')

class TestMustBeASCII(unittest.TestCase):

    ''' Make sure must_be_ascii() works as expected '''

    #
    # With must_be_ascii() we want to guarantee that only ASCII
    # input can reach normalize().  Hence, this test case ensures
    # that we reject nonascii input and we accept ascii input.
    # For each case, ascii and nonascii, we provide both str and
    # bytes input (or, using python2 names, unicode and str).
    #

    def test_nonascii_bytes(self):
        ''' Test must_be_ascii() behavior when input is nonascii bytes '''
        self.assertRaises(UnicodeError, utils_path.must_be_ascii,
                          'cio\xc3\xa8')

    def test_ascii_bytes(self):
        ''' Test must_be_ascii() behavior when input is ascii bytes '''
        self.assertEqual(utils_path.must_be_ascii('abc'), 'abc')

    def test_nonascii_str(self):
        ''' Test must_be_ascii() behavior when input is nonascii str '''
        # Use decode() to avoid declaring file encoding
        self.assertRaises(UnicodeError, utils_path.must_be_ascii,
                          'cio\xc3\xa8'.decode('utf-8'))

    def test_ascii_str(self):
        ''' Test must_be_ascii() behavior when input is ascii str '''
        self.assertEqual(utils_path.must_be_ascii('abc'),
                         'abc'.decode('utf-8'))

class TestNormalize(unittest.TestCase):

    ''' Make sure normalize() works as expected '''

    #
    # With this test case we want to gain confidence that
    # the following assertions are true:
    #
    # 1. that normalize() collapses multiple slashes;
    #
    # 2. that normalize() simplifies redundant up-level refs,
    #    i.e. '../' or '..\\';
    #
    # 3. that normalize() converts / into \\ on Win32;
    #
    # 4. that the result is one of:
    #
    #    4.1. an absolute path without uplevel references;
    #
    #    4.2. a relative path without uplevel references;
    #
    #    4.3. a relative path with one or more uprefs at the
    #         beginning, and no further uprefs after the first
    #         dir or file name.
    #

    def test__1(self):
        ''' Make sure normalize() collapses multiple slashes '''
        self.assertEqual(utils_path.normalize('/foo////bar'),
                         os.sep.join(['', 'foo', 'bar']))

    def test__2(self):
        ''' Make sure normalize() simplifies redundant up-level refs '''
        self.assertEqual(utils_path.normalize('/foo/bar/../baz'),
                         os.sep.join(['', 'foo', 'baz']))

    def test__3(self):
        ''' Make sure normalize() converts / to \\ on windows '''
        if os.name == 'nt':
            self.assertEqual(utils_path.normalize('foo/bar'), r'foo\bar')

    #
    # 4.1.  If you start with an absolute path you will ALWAYS
    # end up with an absolute path, BUT will loose (part of) the
    # leading prefix.  This happens because the parent of / is
    # always / so you cannot go before it using '../'.
    #
    def test__4_1(self):
        ''' Verify normalize() result when input is absolute path '''
        self.assertEqual(utils_path.normalize('/foo/bar/../baz'),
                         ''.join([os.sep, 'foo', os.sep, 'baz']))
        self.assertEqual(utils_path.normalize('/foo/bar/../../baz'),
                         ''.join([os.sep, 'baz']))
        self.assertEqual(utils_path.normalize('/foo/bar/../../../baz'),
                         ''.join([os.sep, 'baz']))
        self.assertEqual(utils_path.normalize('/foo/bar/../../../../baz'),
                         ''.join([os.sep, 'baz']))

    #
    # 4.2. and 4.3.  When the input is relative the general form of
    # the result is: \alpha * '../' + '/' + \beta * $name, where $name
    # of course does not contain any '../'.  \alpha is zero when the
    # real starting point of the path is the "current" node (4.2) and
    # is nonzero when the real starting point is some node above the
    # "current" one (4.3).  When the path is normalized, once you are
    # on the real starting point you don't need any more up-ref, hence
    # the general case formula.  Note that 4.1 is just a special case
    # of this one, where simply \alpha up-refs are ignored because the
    # parent of / is again '/'.
    #
    def test__4_2__and__4_3(self):
        ''' Verify normalize() result when input is relative path '''

        # 4.2 the starting node is the parent of foo
        self.assertEqual(utils_path.normalize('foo/bar/../baz'),
                         os.sep.join(['foo', 'baz']))
        self.assertEqual(utils_path.normalize('foo/bar/../../baz'),
                         'baz')

        # 4.3 the starting node is ABOVE the parent of foo
        self.assertEqual(utils_path.normalize('foo/bar/../../../baz'),
                         os.sep.join(['..', 'baz']))
        self.assertEqual(utils_path.normalize('foo/bar/../../../../baz'),
                         os.sep.join(['..', '..', 'baz']))

class TestMustBeAbsolute(unittest.TestCase):
 
    ''' Make sure must_be_absolute() works as expected '''

    #
    # The return value of normalize may only one of: absolute path
    # and relative path w/o and w/ leading '../'s.  In this test we
    # make sure that the first case is accepted, and that the 2nd
    # and the 3rd cases are rejected.
    #

    def test_success(self):
        ''' Make sure must_be_absolute() recognizes absolute paths '''
        string = ''.join([os.sep, 'foo'])
        self.assertEqual(utils_path.must_be_absolute(string), string)
 
    def test_failure(self):
        ''' Make sure must_be_absolute() bails out on relative paths '''
        string = ''.join(['foo', os.sep, 'bar'])
        self.assertRaises(ValueError, utils_path.must_be_absolute, string)
        string = ''.join(['..', os.sep, 'foo', os.sep, 'bar'])
        self.assertRaises(ValueError, utils_path.must_be_absolute, string)
 
class TestMustNotBeUpref(unittest.TestCase):

    ''' Make sure must_not_be_upref() works as expected '''

    #
    # The return value of normalize may only one of: absolute path
    # and relative path w/o and w/ leading '../'s.  In this test we
    # make sure that the first and second case are accepted, the
    # latter is rejected.
    #

    def test_absolute(self):
        ''' Make sure must_not_be_upref() recognizes absolute paths '''
        string = ''.join([os.sep, 'foo', os.sep, 'bar'])
        self.assertEqual(utils_path.must_not_be_upref(string), string)

    def test_relative_nonupref(self):
        ''' Make sure must_not_be_upref() recognizes nonupref relative paths '''
        string = ''.join(['foo', os.sep, 'bar'])
        self.assertEqual(utils_path.must_not_be_upref(string), string)

    def test_relative_upref(self):
        ''' Make sure must_not_be_upref() bails out on upref relative paths '''
        string = ''.join(['..', os.sep, 'foo', os.sep, 'bar'])
        self.assertRaises(ValueError, utils_path.must_not_be_upref, string)

class TestJoin(unittest.TestCase):

    ''' Make sure join() works as expected '''

    #
    # This test case is JUST to stress that join() is
    # dumb: it only collates the two pieces and DOES
    # NOT normalize any pathseps inside the two pieces,
    # nor it performs any other normalization.
    #

    def test_simple(self):
        ''' Just make sure join() works in the simple case '''
        expected = os.sep.join(['abc', 'def'])
        self.assertEqual(utils_path.join('abc', 'def'), expected)

    def test_with_pathsep(self):
        ''' Just make sure join() works w/ pathseps '''
        expected = os.sep.join(['ab/c', 'd/../ef'])
        self.assertEqual(utils_path.join('ab/c', 'd/../ef'), expected)

if __name__ == '__main__':
    unittest.main()
