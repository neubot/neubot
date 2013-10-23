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
import logging

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.net.poller import POLLER
from neubot.speedtest.client import ClientSpeedtest

from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.defer import Deferred
from neubot.log import STREAMING_LOG
from neubot.notify import NOTIFIER
from neubot.raw_negotiate import RawNegotiate
from neubot.runner_dload import RunnerDload
from neubot.runner_hosts import RUNNER_HOSTS
from neubot.runner_mlabns import RunnerMlabns
from neubot.runner_tests import RUNNER_TESTS

from neubot import bittorrent
from neubot import privacy
from neubot import runner_rendezvous
from neubot import system
from neubot import utils_modules

class RunnerCore(object):

    ''' Implements component that runs the selected test '''

    def __init__(self):
        ''' Initialize component that runs the selected test '''
        self.dynamic_tests = {}
        self.queue = collections.deque()
        self.running = False

    def test_is_running(self):
        ''' Reports whether a test is running '''
        return self.running

    def run(self, test, deferred, auto_discover=True, ctx=None):
        ''' Run test and deferred when done '''

        if (
            test != "rendezvous" and
            test != "speedtest" and
            test != "bittorrent" and
            test != "dload" and
            test != "raw" and
            test != "mlab-ns" and
            test not in self.dynamic_tests
           ):
            utils_modules.modprobe("mod_" + test, "register_test",
                                   self.dynamic_tests)

        if auto_discover:
            logging.info('runner_core: Need to auto-discover first...')

            deferred2 = Deferred()
            deferred2.add_callback(lambda param: None)

            if test == 'raw':
                self.queue.append(('mlab-ns', deferred2, {'policy': 'random'}))

            elif test == "bittorrent" or test == "speedtest":
                self.queue.append(('rendezvous', deferred2, None))

            else:
                try:
                    test_rec = self.dynamic_tests[test]
                    self.queue.append((test_rec["discover_method"],
                      deferred2, {"policy": test_rec["discover_policy"]}))
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    logging.warning("runner: internal error", exc_info=1)

        self.queue.append((test, deferred, ctx))
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
        deferred = Deferred()
        deferred.add_callback(self._do_run_queue)
        deferred.add_errback(self._run_queue_error)
        deferred.callback(self.queue[0])

    @staticmethod
    def _run_queue_error(error):
        ''' Invoked when _do_run_queue() fails '''
        logging.error('runner_core: catched exception: %s', error)
        NOTIFIER.publish('testdone')

    def _do_run_queue(self, first_elem):
        ''' Actually run first element in queue '''

        # Make a copy of current settings
        conf = CONFIG.copy()

        # Make sure we abide to M-Lab policy
        if privacy.count_valid(conf, 'privacy.') != 3:
            privacy.complain()
            raise RuntimeError('runner_core: bad privacy settings')

        elif first_elem[0] == 'rendezvous':
            runner_rendezvous.run(conf['agent.master'], '9773')

        elif first_elem[0] == 'speedtest':
            uri = RUNNER_TESTS.test_to_negotiate_uri('speedtest')
            conf['speedtest.client.uri'] =  uri
            client = ClientSpeedtest(POLLER)
            client.configure(conf)
            client.connect_uri()

        elif first_elem[0] == 'bittorrent':
            uri = RUNNER_TESTS.test_to_negotiate_uri('bittorrent')
            conf['bittorrent._uri'] =  uri
            bittorrent.run(POLLER, conf)

        elif first_elem[0] == 'dload':
            RunnerDload(first_elem[2])

        elif first_elem[0] == 'raw':
            address = RUNNER_HOSTS.get_random_host()
            handler = RawNegotiate()
            handler.connect((address, 8080), CONFIG['prefer_ipv6'], 0, {})

        elif first_elem[0] == 'mlab-ns':
            handler = RunnerMlabns()
            if not first_elem[2]:
                extra = {'policy': ''}  # get closest server by default
            else:
                extra = first_elem[2]
            handler.connect(('mlab-ns.appspot.com', 80),
              CONFIG['prefer_ipv6'], 0, extra)

        elif first_elem[0] in self.dynamic_tests:
            address = RUNNER_HOSTS.get_random_host()
            port = 80  # XXX
            self.dynamic_tests[first_elem[0]]["test_func"]({
                "address": address,
                "conf": CONFIG.copy(),
                "poller": POLLER,
                "port": port,
            })

        else:
            raise RuntimeError('runner_core: asked to run an unknown test')

    def test_done(self, *baton):
        ''' Invoked when the test is done '''

        #
        # Stop streaming test events to interested parties
        # via the log streaming API.
        # Do not stop processing immediately and give HTTP
        # code time to stream logs to the client in case
        # connections fails immediately.
        # This must not be done when we're processing the
        # somewhat internal 'rendezvous' or 'mlab-ns' tests.
        #
        if self.queue[0][0] != 'rendezvous' and self.queue[0][0] != 'mlab-ns':
            POLLER.sched(2, STREAMING_LOG.stop_streaming)

        # Paranoid
        if baton[0] != 'testdone':
            raise RuntimeError('runner_core: invoked for the wrong event')

        # Notify the caller that the test is done
        deferred, ctx = self.queue.popleft()[1:]
        deferred.callback(ctx)

        #
        # Allow for more tests
        # If callback() adds one more test, that would
        # be run by the run_queue() invocation below.
        #
        self.running = False

        # Eventually run next queued test
        self.run_queue()

RUNNER_CORE = RunnerCore()

USAGE = 'usage: neubot runner_core [-nv] [-f dabatase] test [uri]'

def main(args):
    ''' Main function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'f:nv')
    except getopt.error:
        sys.exit(USAGE)

    database_path = system.get_default_database_path()
    auto_discover = True
    for name, value in options:
        if name == '-f':
            database_path = value
        elif name == '-n':
            auto_discover = False
        elif name == '-v':
            CONFIG['verbose'] = 1

    if len(arguments) != 1 and len(arguments) != 2:
        sys.exit(USAGE)

    DATABASE.set_path(database_path)
    CONFIG.merge_database(DATABASE.connection())

    if len(arguments) == 2:
        RUNNER_TESTS.update({arguments[0]: [arguments[1]]})
        ctx = {'uri': arguments[1]}
    else:
        ctx = None

    deferred = Deferred()
    deferred.add_callback(lambda param: None)
    RUNNER_CORE.run(arguments[0], deferred, auto_discover, ctx)
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
