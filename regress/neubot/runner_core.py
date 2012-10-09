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

''' Regression test for runner_core module '''

import unittest
import sys
import logging

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.config import CONFIG
from neubot.defer import Deferred
from neubot.log import LOG
from neubot.notify import NOTIFIER
from neubot.runner_core import RunnerCore
from neubot.runner_tests import RUNNER_TESTS

from neubot import bittorrent
from neubot import privacy

class TestIsRunningTest(unittest.TestCase):
    ''' Regression test for test_is_running() '''

    #
    # We have too many public methods and we know that
    # pylint: disable=R0904
    #

    def test_smpl(self):
        ''' Check behavior is correct when empty '''
        #
        # The most basic test, just make sure that at the
        # beginning the state is consistent and that running
        # the empty queue does not have side effects.
        #
        core = RunnerCore()
        self.assertEqual(core.test_is_running(), False)
        core.run_queue()

class RunQueueTest(unittest.TestCase):
    ''' Regression test for run_queue() '''

    #
    # Possible improvements:
    #
    # - A core assumption of this regression test is that the
    #   ``running`` field is handled consistently.
    #
    # - This regression test does not provide a test for the
    #   speedtest case, because it does not suffice to hook
    #   a single function to run it.
    #
    # We have too many public methods and we know that
    # pylint: disable=R0904
    #

    def test_when_queue_empty(self):
        ''' Verify run_queue() behavior when queue is empty '''
        #
        # It should not run when the queue is empty,
        # if I'm wrong and it runs and it does not
        # crash (unlikely), the self.running attribute
        # would be true.
        #
        core = RunnerCore()
        core.run_queue()
        self.assertFalse(core.running)

    def test_wrong_privacy(self):
        ''' Verify run_queue() behavior when privacy is wrong '''

        #
        # The whole point of this test is to make sure
        # that privacy.complain() is invoked and "testdone"
        # is published when privacy settings are not OK
        # and a test is started.
        #

        # We need to ensure privacy.complain() is invoked
        privacy_complain = [0]
        def on_privacy_complain():
            ''' Register privacy.complain() invokation '''
            privacy_complain[0] += 1

        # Setup (we will restore that later)
        saved_complain = privacy.complain
        privacy.complain = on_privacy_complain

        CONFIG.conf['privacy.informed'] = 0
        core = RunnerCore()
        core.queue.append(('foo', Deferred(), None))
        core.run_queue()

        # Restore
        privacy.complain = saved_complain

        # Worked as expected?
        self.assertTrue(privacy_complain[0])
        self.assertFalse(NOTIFIER.is_subscribed("testdone"))

    def test_bittorrent_invokation_good(self):
        ''' Verify run_queue() behavior when bittorrent is invoked
            and there is a URI for bittorrent '''

        #
        # The whole point of this test is to make sure that
        # bittorrent.run() is invoked when privacy is OK and
        # we have a negotiate URI.  We also want to check that
        # the "testdone" event is subscribed after run_queue(),
        # i.e. that someone is waiting for the event that
        # signals the end of the test.
        #

        # We need to ensure bittorrent.run() is invoked
        bittorrent_run = [0]
        def on_bittorrent_run(poller, conf):
            ''' Register bittorrent.run() invokation '''
            # pylint: disable=W0613
            bittorrent_run[0] += 1

        # Setup (we will restore that later)
        saved_run = bittorrent.run
        bittorrent.run = on_bittorrent_run
        RUNNER_TESTS.update({'bittorrent': '/'})

        CONFIG.conf['privacy.can_publish'] = 1
        CONFIG.conf['privacy.informed'] = 1
        CONFIG.conf['privacy.can_collect'] = 1
        core = RunnerCore()
        core.queue.append(('bittorrent', Deferred(), None))
        core.run_queue()

        # Restore
        bittorrent.run = saved_run
        RUNNER_TESTS.update({})

        # Worked as expected?
        self.assertTrue(bittorrent_run[0])
        self.assertTrue(NOTIFIER.is_subscribed("testdone"))

        #
        # Clear the "testdone" because otherwise it will
        # screw up other tests and we don't want that
        #
        NOTIFIER.publish("testdone")

    def test_safety_net(self):
        ''' Verify run_queue() safety net works '''

        #
        # The whole point of this test is to make sure
        # that and error is printed and "testdone" is
        # published when a new test is started and the
        # test name is bad.
        #

        # We need to ensure logging.error() is invoked
        log_error = [0]
        def on_log_error(message, *args):
            ''' Register logging.error() invokation '''
            # pylint: disable=W0613
            log_error[0] += 1

        # Setup (we will restore that later)
        saved_log_error = logging.error
        logging.error = on_log_error

        CONFIG.conf['privacy.can_publish'] = 1
        CONFIG.conf['privacy.informed'] = 1
        CONFIG.conf['privacy.can_collect'] = 1
        core = RunnerCore()
        core.queue.append(('foo', Deferred(), None))
        core.run_queue()

        # Restore
        logging.error = saved_log_error

        # Worked as expected?
        self.assertTrue(log_error[0])
        self.assertFalse(NOTIFIER.is_subscribed("testdone"))

if __name__ == '__main__':
    unittest.main()
