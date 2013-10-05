#!/usr/bin/env python

#
# Copyright (c) 2012-2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     Simone Basso <bassosimone@gmail.com>
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

import logging
import unittest
import os
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import six
from neubot import utils_path

class TestDepthVisit(unittest.TestCase):
    ''' Make sure that depth_visit() works as expected '''

    #
    # This test case wants to garner confidence that:
    #
    # 1. visit() is not invoked when components is empty;
    #
    # 2. depth_visit() accepts a non-ascii prefix;
    #
    # 3. depth_visit() rejects a non-ascii component;
    #
    # 4. depth_visit() bails out w/ upref components;
    #
    # 5. depth_visit() is more restrictive than needed, and
    #    rejects some paths that are below prefix due to the
    #    way depth_visit() is implemented;
    #
    # 6. depth_visit() visits nodes in the expected order;
    #
    # 7. depth_visit() correctly flags the leaf node.
    #

    def test__1(self):
        ''' Make sure that depth_visit() works OK w/ empty components '''

        visit_called = [0]
        def on_visit_called(*args):
            ''' Just an helper function '''
            visit_called[0] += 1

        utils_path.depth_visit('/foo', [], on_visit_called)

        self.assertFalse(visit_called[0])

    def test__2(self):
        ''' Make sure that depth_visit() accepts a non-ascii prefix '''

        visit = {
            "count": 0,
            "expect_path": [
                six.b("/foo\xc3\xa8").decode("utf-8") + "/bar",
                six.b("/foo\xc3\xa8").decode("utf-8") + "/bar" + "/baz",
            ],
            "expect_leaf": [
                False,
                True
            ],
        }

        def on_visit_called(path, leaf):
            ''' Just an helper function '''
            self.assertEqual(path, visit["expect_path"][visit["count"]])
            self.assertEqual(leaf, visit["expect_leaf"][visit["count"]])
            visit["count"] += 1

        utils_path.depth_visit(six.b('/foo\xc3\xa8'), ['bar',
          'baz'], on_visit_called)

    def test__3(self):
        ''' Make sure that depth_visit() does not accept non-ascii component '''
        self.assertRaises(RuntimeError, utils_path.depth_visit,
          '/foo', ['bar', six.b('baz\xc3\xa8')], lambda *args: None)

    def test__4(self):
        ''' Make sure that depth_visit() fails w/ upref components '''
        self.assertRaises(RuntimeError, utils_path.depth_visit,
          '/foo', ['../../baz/xo'], lambda *args: None)

    def test__5(self):
        ''' Verify that depth_visit() is more restrictive than needed '''
        self.assertRaises(RuntimeError, utils_path.depth_visit,
          '/foo', ['/bar/bar', '../baz/xo'], lambda *args: None)

    def test__6(self):
        ''' Make sure that depth_visit() visits in the expected order '''

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

    def test__7(self):
        ''' Make sure that depth_visit() correctly flags the leaf node '''

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

class TestPossiblyDecode(unittest.TestCase):
    ''' Make sure that possibly() works as expected '''

    #
    # Note: six.u("cio\xe8") is an italian word and means "that
    # is".  I write the word using escapes, because I don't want
    # to add an explicit encoding to this file.
    #

    def test_nonascii_bytes(self):
        ''' Test possibly_decode() with unicode bytes input '''
        self.assertEqual(
            utils_path.possibly_decode('cio\xc3\xa8', 'utf-8'),
            six.u("cio\xe8")
        )

    def test_ascii_bytes(self):
        ''' Test possibly_decode() with ascii bytes input '''
        self.assertEqual(
            utils_path.possibly_decode(six.b('abc'), 'utf-8'),
            six.u('abc')
        )

    def test_nonascii_str(self):
        ''' Test possibly_decode() with unicode string input '''
        self.assertEqual(
            utils_path.possibly_decode(six.u("cio\xe8"), 'utf-8'),
            six.u("cio\xe8")
        )

    def test_ascii_str(self):
        ''' Test possibly_decode() with ascii string input '''
        self.assertEqual(
            utils_path.possibly_decode(six.u("abc"), 'utf-8'),
            six.u("abc")
        )

    def test_decode_failure(self):
        ''' Make sure that possibly_decode() does not decode
            an invalid UTF-8 string '''
        self.assertEqual(
            utils_path.possibly_decode(six.b("\xc2b7"), 'utf-8'),
            None
        )

class TestAppend(unittest.TestCase):
    ''' Make sure that append() works as expected '''

    #
    # This test case wants to gain confidence that the following
    # statements are true:
    #
    # 1. append() fails when it can't decode the prefix or the path;
    #
    # 2. append() unquotes the path, if requested to do so;
    #
    # 3. append() does not allow to go above the rootdir;
    #
    # 4. append() ASCII-fies the path in any case.
    #

    def test__1(self):
        ''' Make sure that append() fails when it can't decode
            the prefix or the path '''
        # Note: '/cio\xc3a8' is wrong on purpose here
        self.assertEqual(
            utils_path.append(six.b('/cio\xc3a8'), '/foobar', False),
            None
        )
        self.assertEqual(
            utils_path.append('/foobar', six.b('/cio\xc3\xa8'), False),
            None
        )

    def test__2(self):
        ''' Verify that append() unquotes the path, if requested to do so '''
        self.assertEqual(
            utils_path.append('/foobar', 'foo%2fbaz', False),
            "/foobar/foo%2fbaz",
        )
        self.assertEqual(
            utils_path.append('/foobar', 'foo%2fbaz', True),
            "/foobar/foo/baz",
        )

    def test__3(self):
        ''' Verify that append() does not allow to go above the rootdir '''
        self.assertEqual(
            utils_path.append('/foobar', '../etc/passwd', False),
            None
        )
        self.assertEqual(
            utils_path.append('/foobar',
                six.b('\x2e\x2e\x2fetc\x2fpasswd'),
                False),
            None
        )
        self.assertEqual(
            utils_path.append('/foobar',
                six.b('..%2fetc%2fpasswd'),
                True),
            None
        )

    def test__4(self):
        ''' Verify that append() ASCII-fies the path in any case '''
        self.assertEqual(
            utils_path.append("/foobar",
                six.u("'/cio\xe8'"), True),
            None
        )
        self.assertEqual(
            utils_path.append("/foobar",
                six.u("'/cio%e8'"), True),
            None
        )

class TestNormalize(unittest.TestCase):
    ''' Make sure that normalize() works as expected '''

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
        ''' Make sure that normalize() collapses multiple slashes '''
        self.assertEqual(utils_path.normalize('/foo////bar'),
                         os.sep.join(['', 'foo', 'bar']))

    def test__2(self):
        ''' Make sure that normalize() simplifies redundant up-level refs '''
        self.assertEqual(utils_path.normalize('/foo/bar/../baz'),
                         os.sep.join(['', 'foo', 'baz']))

    def test__3(self):
        ''' Make sure that normalize() converts / to \\ on windows '''
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

class TestJoin(unittest.TestCase):
    ''' Make sure that join() works as expected '''

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
    logging.basicConfig(level=logging.ERROR)  # silence, please
    unittest.main()
