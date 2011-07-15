# neubot/api/client.py

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

import types
import time
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.http.message import Message
from neubot.http.client import ClientHTTP
from neubot.net.poller import POLLER
from neubot.compat import json
from neubot.log import LOG
from neubot.main import common

class APIStateTracker(ClientHTTP):

    """Polls the state of the Neubot daemon and prints the JSON
       object representing the state on the standard output.

       Subclasses might want to override the method that prints
       to stdout, in order to implement something smarter.

       This class allows the controller to live into another
       thread of execution, and implements a safe mechanism that
       allows to interrupt the polling."""

    def __init__(self, poller):
        ClientHTTP.__init__(self, poller)
        self.timestamp = 0
        self.uri = ""
        self.stop = False

    #
    # Do not assume that the controller lives in the same thread
    # of execution we live in.  So, run in a loop and provide a mean
    # to force to break out of the loop: the controlling code just
    # need to call interrupt().
    #

    def interrupt(self):
        self.stop = True

    def loop(self):
        while not self.stop:
            self.start_transaction()
            POLLER.loop()
            # We should land here on errors only
            time.sleep(3)

    def start_transaction(self, stream=None):

        #
        # XXX This is complexity at the wrong level of abstraction
        # because the HTTP client should manage more than one connections
        # and we should just pass it HTTP messages and receive events
        # back.
        #

        if not stream:
            endpoint = (self.conf.get("api.client.address", "127.0.0.1"),
                        int(self.conf.get("api.client.port", "9774")))
            self.connect(endpoint)

        else:

            uri = "http://%s:%s/api/state?t=%d" % (
              self.conf.get("api.client.address", "127.0.0.1"),
              self.conf.get("api.client.port", "9774"),
              self.timestamp)

            request = Message()
            request.compose(method="GET", uri=uri)

            stream.send_request(request)

    def connection_ready(self, stream):
        self.start_transaction(stream)

    def got_response(self, stream, request, response):

        try:
            self.check_response(response)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            LOG.exception()
            time.sleep(3)

        del request
        del response

        self.start_transaction(stream)

    def check_response(self, response):

        if response.code != "200":
            raise ValueError("Bad HTTP response code")
        if response["content-type"] != "application/json":
            raise ValueError("Unexpected contenty type")

        octets = response.body.read()
        dictionary = json.loads(octets)

        LOG.debug("APIStateTracker: received JSON: " +
            json.dumps(dictionary, ensure_ascii=True))

        if not "events" in dictionary:
            return

        if not "current" in dictionary:
            raise ValueError("Incomplete dictionary")

        t = dictionary["t"]
        if not type(t) == types.IntType and not type(t) == types.LongType:
            raise ValueError("Invalid type for current event time")
        if t < 0:
            raise ValueError("Invalid value for current event time")

        self.timestamp = t
        self.process_dictionary(dictionary)

    def process_dictionary(self, dictionary):
        octets = json.dumps(dictionary)
        sys.stdout.write(octets)
        sys.stdout.write("\n\n")

CONFIG.register_defaults({
    "api.client.address": "127.0.0.1",
    "api.client.port": "9774",
})

def main(args):

    CONFIG.register_descriptions({
        "api.client.address": "Set address to connect to",
        "api.client.port": "Set port to connect to",
    })

    common.main("api.client", "Minimal client for JSON API", args)
    client = APIStateTracker(POLLER)
    client.configure(CONFIG.copy())
    client.loop()

if __name__ == "__main__":
    main(sys.argv)
