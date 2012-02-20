# neubot/rendezvous/client.py

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

''' Rendezvous client '''

#
# This file contains the client that periodically connects
# to the master server to get next-test and available-updates
# information.
#

import os
import random
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.net.poller import POLLER

from neubot.config import CONFIG
from neubot.log import LOG
from neubot.main import common
from neubot.notifier_browser import NOTIFIER_BROWSER
from neubot.runner_core import RUNNER_CORE
from neubot.runner_tests import RUNNER_TESTS
from neubot.runner_updates import RUNNER_UPDATES
from neubot.state import STATE

from neubot import privacy

def _open_browser_on_windows(page):

    ''' Open a browser in the user session to notify something '''

    #
    # This is possible only on Windows, where we run in the same
    # context of the user.  I contend that opening the browser is
    # a bit brute force, but it works.  If you have patches that
    # allow to deploy lowoverhead notifications email me.
    #

    if os.name == 'nt':
        NOTIFIER_BROWSER.notify_page(page)

class ClientRendezvous(object):

    ''' Rendezvous client '''

    def __init__(self):
        ''' Initializer '''
        self._interval = 0

    def _after_rendezvous(self):
        ''' After rendezvous actions '''

        #
        # If rendezvous fails, RUNNER_UPDATES and RUNNER_TESTS
        # may be empty.  In such case, this function becomes just
        # a no operation and nothing happens.
        #

        # Inform the user when we have updates
        new_version = RUNNER_UPDATES.get_update_version()
        new_uri = RUNNER_UPDATES.get_update_uri()
        if new_version and new_uri:
            LOG.info("Version %s available at %s" % (new_version,
                                                     new_uri))
            STATE.update("update", {"version": new_version,
                                    "uri": new_uri})
            _open_browser_on_windows('update.html')

        #
        # Choose the test we would like to run even if
        # we're not going to run it because we're running
        # in debug mode or tests are disabled.
        # This allows us to print to the logger the test
        # we /would/ have choosen if we were allowed to run
        # it.
        #
        test = RUNNER_TESTS.get_next_test()
        if not test:
            LOG.warning("No test available")
            self._schedule()
            return

        LOG.info("* Chosen test: %s" % test)

        # Are we allowed to run a test?
        if not CONFIG["enabled"] or CONFIG["rendezvous.client.debug"]:
            LOG.info("Tests are disabled... not running")
            self._schedule()
            return

        # Actually run the test
        RUNNER_CORE.run(test, self._schedule)

    def _schedule(self):

        ''' Schedule next rendezvous '''

        #
        # Typically the user does not specify the interval
        # and we use a random value around 1500 seconds.
        # The random value is extracted just once and from
        # that point on we keep using it.
        # Suggested by Elias S.G. Carotti some time ago.
        #
        interval = CONFIG["agent.interval"]
        if not interval:
            if not self._interval:
                self._interval = 1380 + random.randrange(0, 240)
            interval = self._interval

        LOG.info("* Next rendezvous in %d seconds" % interval)

        task = POLLER.sched(interval, self.run)

        STATE.update("idle", publish=False)
        STATE.update("next_rendezvous", task.timestamp)

    def run(self):
        ''' Periodically run rendezvous '''

        if not privacy.allowed_to_run():
            _open_browser_on_windows('privacy.html')
            # Except from opening the browser, privacy actions are
            # now performed by RUNNER_CORE

        RUNNER_CORE.run('rendezvous', self._after_rendezvous)

CONFIG.register_defaults({
    "rendezvous.client.debug": False,
    "rendezvous.client.version": common.VERSION,
})

def main(args):

    ''' Main function '''

    CONFIG.register_descriptions({
        "rendezvous.client.debug": "Do not perform any test",
        "rendezvous.client.version": "Set rendezvous client version",
    })

    common.main("rendezvous.client", "Rendezvous client", args)

    client = ClientRendezvous()
    client.run()

    POLLER.loop()
