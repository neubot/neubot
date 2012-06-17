# neubot/runner_core.py

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

''' Component that runs the selected test '''

#
# This is the component that allows for running tests
# on demand both from command line and from the web
# user interface of Neubot.
#

import asyncore
import collections
import getopt
import sys
import logging

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.net.poller import POLLER
from neubot.speedtest.client import ClientSpeedtest
from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.log import STREAMING_LOG
from neubot.notify import NOTIFIER
from neubot.runner_tests import RUNNER_TESTS
from neubot.runner_dload import RunnerDload

from neubot import bittorrent
from neubot import privacy
from neubot import runner_rendezvous
from neubot import system

class RunnerCore(object):

    ''' Implements component that runs the selected test '''

    def __init__(self):
        ''' Initialize component that runs the selected test '''
        self.queue = collections.deque()
        self.running = False

    def test_is_running(self):
        ''' Reports whether a test is running '''
        return self.running

    def run(self, test, callback, auto_rendezvous=True, ctx=None):
        ''' Run test and callback() when done '''

        #
        # If we are about to run a test and the list of
        # available tests is empty, we need certainly to
        # refill it before proceeding.
        #
        if (auto_rendezvous and test != 'rendezvous' and
            len(RUNNER_TESTS.get_test_names()) == 0):
            logging.info('runner_core: Need to rendezvous first...')
            self.queue.append(('rendezvous', lambda: None, None))

        self.queue.append((test, callback, ctx))
        self.run_queue()

    def run_queue(self):
        ''' If possible run the first test in queue '''

        # Adapted from neubot/rendezvous/client.py

        if not self.queue:
            return
        if self.running:
            return

        #
        # Subscribe BEFORE starting the test, otherwise we
        # may miss the 'testdone' event if the connection
        # to the negotiator service fails, and we will stay
        # stuck forever.
        #
        NOTIFIER.subscribe('testdone', self.test_done)

        # Prevent concurrent tests
        self.running = True

        # Safely run first element in queue
        try:
            self._do_run_queue()
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            exc = asyncore.compact_traceback()
            error = str(exc)
            logging.error('runner_core: catched exception: %s', error)
            NOTIFIER.publish('testdone')

    def _do_run_queue(self):
        ''' Actually run first element in queue '''

        # Make a copy of current settings
        conf = CONFIG.copy()

        # Make sure we abide to M-Lab policy
        if privacy.count_valid(conf, 'privacy.') != 3:
            privacy.complain()
            raise RuntimeError('Bad privacy settings')

        # Run rendezvous
        elif self.queue[0][0] == 'rendezvous':
            runner_rendezvous.run(conf['agent.master'])

        # Run speedtest
        elif self.queue[0][0] == 'speedtest':
            uri = RUNNER_TESTS.test_to_negotiate_uri('speedtest')
            #
            # If we have no negotiate URI for this test, possibly
            # because we are offline, abort it.
            #
            if not uri:
                raise RuntimeError('No negotiate URI for speedtest')
            conf['speedtest.client.uri'] =  uri
            client = ClientSpeedtest(POLLER)
            client.configure(conf)
            client.connect_uri()

        # Run bittorrent
        elif self.queue[0][0] == 'bittorrent':
            uri = RUNNER_TESTS.test_to_negotiate_uri('bittorrent')
            #
            # If we have no negotiate URI for this test, possibly
            # because we are offline, abort it.
            #
            if not uri:
                raise RuntimeError('No negotiate URI for bittorrent')
            conf['bittorrent._uri'] =  uri
            bittorrent.run(POLLER, conf)

        # Run dload
        elif self.queue[0][0] == 'dload':
            RunnerDload(self.queue[0][2])

        # Safety net
        else:
            raise RuntimeError('Asked to run an unknown test')

    def test_done(self, *baton):
        ''' Invoked when the test is done '''

        #
        # Stop streaming test events to interested parties
        # via the log streaming API.
        # Do not stop processing immediately and give HTTP
        # code time to stream logs to the client in case
        # connections fails immediately.
        # This must not be done when we're processing the
        # somewhat internal 'rendezvous' test.
        #
        if self.queue[0][0] != 'rendezvous':
            POLLER.sched(2, STREAMING_LOG.stop_streaming)

        # Paranoid
        if baton[0] != 'testdone':
            raise RuntimeError('Invoked for the wrong event')

        # Notify the caller that the test is done
        callback, ctx = self.queue.popleft()[1:]
        try:
            if ctx:
                callback(ctx)
            else:
                callback()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            exc = asyncore.compact_traceback()
            error = str(exc)
            logging.error('runner_core: catched exception: %s', error)

        #
        # Allow for more tests
        # If callback() adds one more test, that would
        # be run by the run_queue() invocation below.
        #
        self.running = False

        # Eventually run next queued test
        self.run_queue()

RUNNER_CORE = RunnerCore()

def main(args):
    ''' Main function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'f:n')
    except getopt.error:
        sys.exit('Usage: %s [-n] [-f database] test [negotiate_uri]' % args[0])
    if len(arguments) != 1 and len(arguments) != 2:
        sys.exit('Usage: %s [-n] [-f database] test [negotiate_uri]' % args[0])

    database_path = system.get_default_database_path()
    auto_rendezvous = True
    for name, value in options:
        if name == '-f':
            database_path = value
        elif name == '-n':
            auto_rendezvous = False

    DATABASE.set_path(database_path)
    CONFIG.merge_database(DATABASE.connection())

    if len(arguments) == 2:
        RUNNER_TESTS.update({arguments[0]: [arguments[1]]})
        ctx = {'uri': arguments[1]}
    else:
        ctx = None

    RUNNER_CORE.run(arguments[0], lambda *args: None, auto_rendezvous, ctx)
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
