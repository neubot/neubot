# neubot/rendezvous/client.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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

from neubot.http.client import ClientHTTP
from neubot.http.message import Message
from neubot.net.poller import POLLER

from neubot.config import CONFIG
from neubot.log import LOG
from neubot.main import common
from neubot.notifier_browser import NOTIFIER_BROWSER
from neubot.rendezvous import compat
from neubot.runner_core import RUNNER_CORE
from neubot.runner_tests import RUNNER_TESTS
from neubot.state import STATE

from neubot import marshal
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

class ClientRendezvous(ClientHTTP):
    def __init__(self, poller):
        ClientHTTP.__init__(self, poller)
        self._interval = 0
        self._task = None

    def connect_uri(self, uri=None, count=None):
        self._task = None

        if not privacy.allowed_to_run():
            _open_browser_on_windows('privacy.html')
            privacy.complain()
            self._schedule()
            return

        if not uri:
            uri = "http://%s:9773/rendezvous" % CONFIG["agent.master"]

        LOG.start("* Rendezvous with %s" % uri)
        STATE.update("rendezvous")

        # We need to make just one connection
        ClientHTTP.connect_uri(self, uri, 1)

    def connection_failed(self, connector, exception):
        STATE.update("rendezvous", {"status": "failed"})
        self._schedule()

    def connection_lost(self, stream):
        if RUNNER_CORE.test_is_running():
            LOG.debug("RendezVous: don't _schedule(): test in progress")
            return
        if self._task:
            LOG.debug("RendezVous: don't _schedule(): we already have a task")
            return
        self._schedule()

    def connection_ready(self, stream):
        LOG.progress()

        m = compat.RendezvousRequest()
        m.accept.append("speedtest")
        m.accept.append("bittorrent")
        m.version = CONFIG["rendezvous.client.version"]
        m.privacy_informed = CONFIG['privacy.informed']
        m.privacy_can_collect = CONFIG['privacy.can_collect']
        m.privacy_can_share = CONFIG['privacy.can_publish']             # XXX

        request = Message()
        request.compose(method="GET", pathquery="/rendezvous",
          mimetype="text/xml", keepalive=False, host=self.host_header,
          body=marshal.marshal_object(m, "text/xml"))

        stream.send_request(request)

    def got_response(self, stream, request, response):
        if response.code != "200":
            LOG.complete("bad response")
            self._schedule()
        else:
            LOG.complete()
            s = response.body.read()
            try:
                m1 = marshal.unmarshal_object(s, "application/json",
                  compat.RendezvousResponse)
            except ValueError:
                LOG.exception()
                self._schedule()
            else:
                if "version" in m1.update and "uri" in m1.update:
                    ver, uri = m1.update["version"], m1.update["uri"]
                    LOG.info("Version %s available at %s" % (ver, uri))
                    STATE.update("update", {"version": ver, "uri": uri})
                    _open_browser_on_windows('update.html')

                # Update tests known by the runner
                RUNNER_TESTS.update(m1.available)

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
                else:

                    # Actually run the test
                    RUNNER_CORE.run(test, self._schedule)

    def _schedule(self):

        #
        # Typically the user does not specify the interval
        # and we use a random value around 1500 seconds.
        # The random value is extracted just once and from
        # that point on we keep using it.
        #
        interval = CONFIG["agent.interval"]
        if not interval:
            if not self._interval:
                self._interval = 1380 + random.randrange(0, 240)
            interval = self._interval

        LOG.info("* Next rendezvous in %d seconds" % interval)

        fn = lambda *args, **kwargs: self.connect_uri()
        self._task = POLLER.sched(interval, fn)

        STATE.update("idle", publish=False)
        STATE.update("next_rendezvous", self._task.timestamp)

CONFIG.register_defaults({
    "rendezvous.client.debug": False,
    "rendezvous.client.version": common.VERSION,
})

def main(args):

    CONFIG.register_descriptions({
        "rendezvous.client.debug": "Do not perform any test",
        "rendezvous.client.version": "Set rendezvous client version",
    })

    common.main("rendezvous.client", "Rendezvous client", args)
    conf = CONFIG.copy()

    client = ClientRendezvous(POLLER)
    client.configure(conf)
    client.connect_uri()

    POLLER.loop()
