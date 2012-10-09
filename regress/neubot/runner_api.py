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

''' Regression test for runner_api module '''

import unittest
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.config import ConfigError
from neubot.log import STREAMING_LOG
from neubot.runner_api import runner_api
from neubot.runner_core import RUNNER_CORE
from neubot.runner_tests import RUNNER_TESTS

class RegressionTestStream(object):
    ''' Stream for this regression test '''

    #
    # We have just one public method and
    # we don't use all arguments.
    #
    # pylint: disable=R0903,W0613
    #

    def __init__(self):
        ''' Initialize stream for this regression test '''
        self.response = None

    def send_response(self, request, response):
        ''' Pretend to send response '''
        self.response = response

class RegressionTest(unittest.TestCase):
    ''' Regression test for runner_api module '''

    #
    # We have too many public methods and we know that
    # pylint: disable=R0904
    #

    def test_no_query(self):
        ''' Make sure we return an empty response when there is no query '''

        #
        # Basically invoke the API without a query and make
        # sure that common response fields are as expected
        #

        stream = RegressionTestStream()
        runner_api(stream, None, '')

        self.assertEqual(stream.response.code, '200')
        self.assertEqual(stream.response.reason, 'Ok')
        self.assertEqual(stream.response['content-type'],
                         'application/json')
        self.assertEqual(stream.response['content-length'], '2')
        self.assertEqual(stream.response.body, '{}')

    def test_missing_test(self):
        ''' Make sure we raise ConfigError if test name is missing '''

        #
        # Provide a completely random query that does not contain
        # the test parameter and make sure that the code raises
        # a ConfigError as expected.
        #

        self.assertRaises(ConfigError, runner_api, None, None, 'foo=bar')

    def test_simple_case(self):
        ''' Make sure that we start the test in the simplest case '''

        #
        # In this case we want to make sure that if we pass a known
        # test name and we don't request for streaming:
        #
        # 1. RUNNER_CORE.run() is invoked;
        #
        # 2. the HTTP response is OK.
        #

        #
        # We need to override the run() function of RUNNER_CORE
        # because we just want to test that it was invoked using
        # the right parameters, not to invoke it.
        #
        run_invoked = [0]
        def on_run_invoked(test, callback, auto_discover, ctx):
            ''' Convenience function to notify that run was invoked '''
            # pylint: disable=W0613
            run_invoked[0] += 1

        # Prerequisites (we will restore original funcs later)
        RUNNER_TESTS.avail = {'bittorrent': 'foo'}
        saved_run = RUNNER_CORE.run
        RUNNER_CORE.run = on_run_invoked

        # Invoke runner_api() for an known test
        stream = RegressionTestStream()
        runner_api(stream, None, 'test=bittorrent')

        # Undo prerequisites
        RUNNER_CORE.run = saved_run
        RUNNER_TESTS.avail = {}

        #
        # We must make sure that run() was invoked and that
        # the response contains precisely what we expect.
        #

        # Make sure that run() was invoked
        self.assertTrue(run_invoked[0])

        # Check response
        self.assertEqual(stream.response.code, '200')
        self.assertEqual(stream.response.reason, 'Ok')
        self.assertEqual(stream.response['content-type'], 'application/json')
        self.assertEqual(stream.response['content-length'], '2')
        self.assertEqual(stream.response.body, '{}')

    def test_streaming_case(self):
        ''' Make sure streaming case works as expected '''

        #
        # In this case we want to make sure that if we pass a known
        # test name and we request for streaming:
        #
        # 1. RUNNER_CORE.run() is invoked;
        #
        # 2. the HTTP response is OK;
        #
        # 3. STREAMING_LOG.start_streaming() is invoked.
        #

        #
        # We need to override the run() function of RUNNER_CORE
        # and start_streaming of STREAMING_LOG because we just want to
        # test that they were invoked using the right parameters,
        # not to invoke them.
        #
        start_streaming_invoked = [0]
        def on_start_streaming_invoked(stream):
            ''' Convenience function to notify that start_streaming
                was invoked '''
            # pylint: disable=W0613
            start_streaming_invoked[0] += 1

        run_invoked = [0]
        def on_run_invoked(test, callback, auto_discover, ctx):
            ''' Convenience function to notify that run was invoked '''
            # pylint: disable=W0613
            run_invoked[0] += 1

        # Prerequisites (we will restore everything later)
        RUNNER_TESTS.avail = {'bittorrent': 'foo'}
        saved_run = RUNNER_CORE.run
        saved_start_streaming = STREAMING_LOG.start_streaming
        RUNNER_CORE.run = on_run_invoked
        STREAMING_LOG.start_streaming = on_start_streaming_invoked

        # Invoke runner_api()
        stream = RegressionTestStream()
        runner_api(stream, None, 'test=bittorrent&streaming=1')

        # Undo prerequisites
        RUNNER_CORE.run = saved_run
        RUNNER_TESTS.avail = {}
        STREAMING_LOG.start_streaming = saved_start_streaming

        #
        # We must make sure that run() was invoked, that STREAMING_LOG's
        # start_streaming was invoked and that the response
        # contains precisely what we expect.
        #

        # Make sure that start_streaming() was invoked
        self.assertTrue(start_streaming_invoked[0])

        # Make sure that run() was invoked
        self.assertTrue(run_invoked[0])

        # Check response
        self.assertEqual(stream.response.code, '200')
        self.assertEqual(stream.response.reason, 'Ok')
        self.assertEqual(stream.response['content-type'], 'text/plain')
        self.assertEqual(stream.response['content-length'], '')
        self.assertEqual(stream.response.body.tell(), 0)

    def test_already_running(self):
        ''' Make sure we cannot start or schedule a test when
            one is already in progress '''

        #
        # If .running is True we expect run_queue() will
        # raise a ConfigError.
        #

        # Prerequisites (we will restore them later)
        RUNNER_CORE.running = True

        # Check
        self.assertRaises(ConfigError, runner_api, None, None,
                          'test=bittorrent')

        # Undo prerequisites
        RUNNER_CORE.running = False

if __name__ == '__main__':
    unittest.main()
