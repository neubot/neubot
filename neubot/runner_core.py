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

import collections
import getopt
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.net.poller import POLLER
from neubot.speedtest.client import ClientSpeedtest
from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.log import LOG
from neubot.notify import NOTIFIER
from neubot import bittorrent
from neubot import privacy
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

    def run(self, test, negotiate_uri, callback):
        ''' Run test using negotiate URI and callback() to notify
            that the test is done '''
        self.queue.append((test, negotiate_uri, callback))
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

        # Make a copy of current settings
        conf = CONFIG.copy()

        # Make sure we abide to M-Lab policy
        if privacy.count_valid(conf, 'privacy.') != 3:
            privacy.complain()
            NOTIFIER.publish('testdone')

        # Run speedtest
        elif self.queue[0][0] == 'speedtest':
            conf['speedtest.client.uri'] =  self.queue[0][1]
            client = ClientSpeedtest(POLLER)
            client.configure(conf)
            client.connect_uri()

        # Run bittorrent
        elif self.queue[0][0] == 'bittorrent':
            conf['bittorrent._uri'] =  self.queue[0][1]
            bittorrent.run(POLLER, conf)

        # Safety net
        else:
            LOG.error('Asked to run an unknown test')
            NOTIFIER.publish('testdone')

    def test_done(self, *baton):
        ''' Invoked when the test is done '''

        #
        # Stop streaming test events to interested parties
        # via the log streaming API.
        #
        LOG.stop_streaming()

        # Paranoid
        if baton[0] != 'testdone':
            raise RuntimeError('Invoked for the wrong event')

        # Notify the caller that the test is done
        callback = self.queue.popleft()[2]
        callback()

        #
        # Allow for more tests
        # If callback() adds one more test, that would
        # be run by the run_queue() invocation below.
        #
        self.running = False

        # Eventually run next queued test
        self.run_queue()

RUNNER_CORE = RunnerCore()

def run(test, negotiate_uri, callback):
    ''' Run test using negotiate URI and callback() to
        notify that the test is done '''
    RUNNER_CORE.run(test, negotiate_uri, callback)

def test_is_running():
    ''' Reports whether a test is running '''
    return RUNNER_CORE.test_is_running()

def main(args):
    ''' Main function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'f')
    except getopt.error:
        sys.exit('Usage: %s [-f database] test negotiate_uri' % args[0])
    if len(arguments) != 2:
        sys.exit('Usage: %s [-f database] test negotiate_uri' % args[0])

    database_path = system.get_default_database_path()
    for name, value in options:
        if name == '-f':
            database_path = value

    DATABASE.set_path(database_path)
    CONFIG.merge_database(DATABASE.connection())

    run(arguments[0], arguments[1], lambda: None)
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
