# neubot/background_rendezvous.py

#
# Copyright (c) 2011-2012 Simone Basso <bassosimone@gmail.com>,
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

''' Runs rendezvous for the background module '''

# Formerly neubot/rendezvous/client.py

#
# Nowadays rendezvous logic is implemented by runner_rendezvous.py
# in terms of runner_core.py.  This file is now just a wrapper around
# runner_rendezvous.py: it periodically runs a rendezvous and then
# attempts to run a test.  It also notifies the user the availability
# of updates, if that is the case.
#

import getopt
import logging
import os
import random
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.config import CONFIG
from neubot.defer import Deferred
from neubot.notifier_browser import NOTIFIER_BROWSER
from neubot.poller import POLLER
from neubot.runner_core import RUNNER_CORE
from neubot.runner_policy import RUNNER_POLICY
from neubot.runner_updates import RUNNER_UPDATES
from neubot.state import STATE

from neubot import privacy

class BackgroundRendezvous(object):
    ''' Runs rendezvous for the background module '''

    def __init__(self):
        self.interval = 0

    @staticmethod
    def _open_browser_on_windows(page):
        ''' Open a browser in the user session to notify something '''
        #
        # This is possible only on Windows, where we run in the same
        # context of the user.  I contend that opening the browser is
        # a bit brute force, but it works.  This is now mitigated by
        # code that ensures Neubot does not notify the user too often.
        # If you are annoyed by that and have time, please consider
        # contributing a PyWin32 notification mechanism.
        #
        if os.name == 'nt':
            NOTIFIER_BROWSER.notify_page(page)

    def _after_rendezvous(self, unused):
        ''' After rendezvous actions '''

        #
        # This function is invoked both when the rendezvous fails
        # and succeeds.  If it succeeds, OK we have fresh information
        # on available tests and updates and we use it.  Otherwise,
        # if rendezvous fails, we may either have old information, or
        # no information, if this is the first rendezvous.  In any
        # case, we do our best to use the available information.
        #

        logging.info('background_rendezvous: automatic rendezvous... done')

        # Inform the user when we have updates
        new_version = RUNNER_UPDATES.get_update_version()
        new_uri = RUNNER_UPDATES.get_update_uri()
        if new_version and new_uri and not CONFIG['win32_updater']:
            logging.info('runner_rendezvous: version %s available at %s',
                         new_version, new_uri)
            STATE.update('update', {'version': new_version,
                                    'uri': new_uri})
            self._open_browser_on_windows('update.html')

        #
        # Choose the test we would like to run even if
        # we're not going to run it because tests are
        # disabled.  So we can print the test name also
        # when tests are disabled.
        #
        # Note: we pick a test at random because now we
        # have a fixed probability of running a test.
        #
        test = RUNNER_POLICY.get_random_test()
        logging.info('background_rendezvous: chosen test: %s', test)

        # Are we allowed to run a test?
        if not CONFIG['enabled']:
            raise RuntimeError('background_rendezvous: automatic '
                               'tests disabled')

        #
        # The two legacy tests, speedtest and bittorent, use the rendezvous
        # to discover the servers. Other tests use mlab-ns.
        #
        use_mlabns = (test != 'speedtest' and test != 'bittorrent')

        # Actually run the test
        deferred = Deferred()
        deferred.add_callback(self._schedule)
        RUNNER_CORE.run(test, deferred, use_mlabns, None)

    def _schedule(self, exception):
        ''' Schedule next rendezvous '''
        if exception:
            logging.warning('background_rendezvous: exception while processing'
                            ' rendezvous response: %s', exception)
        #
        # Typically the user does not specify the interval
        # and we use a random value around 1500 seconds.
        # The random value is extracted just once and from
        # that point on we keep using it.
        # Suggested by Elias S.G. Carotti some time ago.
        #
        interval = CONFIG['agent.interval']
        if not interval:
            if not self.interval:
                self.interval = 1380 + random.randrange(0, 240)
            interval = self.interval
        self._schedule_after(interval)

    def _schedule_after(self, interval):
        ''' Schedule next rendezvous after interval seconds '''
        logging.info('background_rendezvous: next rendezvous in %d seconds',
                     interval)
        timestamp = POLLER.sched(interval, self.run)
        STATE.update('idle', publish=False)
        STATE.update('next_rendezvous', timestamp)

    def start(self):
        ''' Start automatic rendezvous '''
        # Give the system some minutes to settle
        self._schedule_after(300)

    def run(self):
        ''' Periodically run rendezvous '''
        #
        # Except from opening the browser, privacy actions are
        # now performed by RUNNER_CORE
        #
        if not privacy.allowed_to_run():
            self._open_browser_on_windows('privacy.html')
        logging.info('background_rendezvous: automatic rendezvous...')
        deferred = Deferred()
        deferred.add_callback(self._after_rendezvous)
        deferred.add_errback(self._schedule)
        RUNNER_CORE.run('rendezvous', deferred, False, None)

BACKGROUND_RENDEZVOUS = BackgroundRendezvous()

def main(args):
    ''' Main() function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'ni:vy')
    except getopt.error:
        sys.exit('usage: neubot background_rendezvous [-nvy] [-i interval]')
    if arguments:
        sys.exit('usage: neubot background_rendezvous [-nvy] [-i interval]')

    notest = False
    fakeprivacy = False
    interval = 0
    for name, value in options:
        if name == '-n':
            notest = True
        elif name == '-i':
            interval = int(value)
        elif name == '-v':
            CONFIG['verbose'] = 1
        elif name == '-y':
            fakeprivacy = True

    # Fake privacy settings
    if fakeprivacy:
        CONFIG['privacy.informed'] = 1
        CONFIG['privacy.can_collect'] = 1
        CONFIG['privacy.can_publish'] = 1

    if notest:
        CONFIG['enabled'] = 0

    if interval:
        CONFIG['agent.interval'] = interval

    BACKGROUND_RENDEZVOUS.run()
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
