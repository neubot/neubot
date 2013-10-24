# mod_dash/client_negotiate.py

#
# Copyright (c) 2010-2011, 2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

""" The MPEG DASH test negotiator """

# Adapted from neubot/bittorrent/client.py

import logging

from mod_dash.client_smpl import DASHClientSmpl

from neubot.http.client import ClientHTTP
from neubot.http.message import Message

from neubot.backend import BACKEND
from neubot.compat import json
from neubot.notify import NOTIFIER
from neubot.state import STATE

from neubot import utils
from neubot import utils_net

STATE_NEGOTIATE = 0
STATE_COLLECT = 1

# Note: the rates are in Kbit/s
DASH_RATES = [
    100,
    150,
    200,
    250,
    300,
    400,
    500,
    700,
    900,
    1200,
    1500,
    2000,
    2500,
    3000,
    4000,
    5000,
    6000,
    7000,
    10000,
    20000
]

MAX_ITERATIONS = 512

class DASHNegotiateClient(ClientHTTP):
    """ Negotiate client for MPEG DASH test """

    def __init__(self, poller):
        ClientHTTP.__init__(self, poller)

        STATE.update("test_latency", "---", publish=False)
        STATE.update("test_download", "---", publish=False)
        STATE.update("test_upload", "---", publish=False)
        STATE.update("test_progress", "0%", publish=False)
        STATE.update("test_name", "dash")

        self.state = STATE_NEGOTIATE

        self.stream = None
        self.measurements = []
        self.client = None

        self.authorization = ""
        self.real_address = ""
        self.queue_pos = 0
        self.unchoked = False

        self.iterations = 0

    def connect(self, endpoint, count=1):
        if count != 1:
            raise RuntimeError("dash: invalid count")
        logging.info("dash: negotiate with: %s",
            utils_net.format_epnt(endpoint))
        ClientHTTP.connect(self, endpoint, count)

    def connect_uri(self, uri=None, count=None):
        # Note: to discourage people from using connect_uri()
        raise RuntimeError("dash: please, use connect()")

    def connection_ready(self, stream):

        if self.iterations > MAX_ITERATIONS:
            raise RuntimeError("dash: too many negotiations")
        self.iterations += 1

        STATE.update("negotiate")
        logging.info("dash: negotiate... in progress")

        body = json.dumps({
            "dash_rates": DASH_RATES,
        })

        request = Message()
        request.compose(method="POST", pathquery="/negotiate/dash",
          host=self.host_header, body=body, mimetype="application/json")

        request["authorization"] = self.authorization

        stream.set_timeout(300)

        stream.send_request(request)

    def got_response(self, stream, request, response):

        if response.code != "200":
            logging.warning("dash: http request error: %s", response.code)
            stream.close()
            return

        if self.state == STATE_NEGOTIATE:

            response_body = json.load(response.body)

            #
            # Note: the following are the standard fields that
            # the negotiate API call MUST return.
            #
            self.authorization = response_body["authorization"]
            self.queue_pos = response_body["queue_pos"]
            self.real_address = response_body["real_address"]
            self.unchoked = response_body["unchoked"]

            if not self.unchoked:
                logging.info("dash: negotiate... done (queue pos %d)",
                             self.queue_pos)
                STATE.update("negotiate", {"queue_pos": self.queue_pos})
                self.connection_ready(stream)
                return

            logging.info("dash: negotiate... done (unchoked)")

            self.stream = stream

            #
            # The server may override the vector of rates with a "better"
            # vector of rates of its choice.
            #
            rates = list(response_body.get("dash_rates", DASH_RATES))

            self.client = DASHClientSmpl(self.poller, self, rates)
            self.client.configure(self.conf.copy())
            self.client.connect((self.stream.peername[0], 80))  # XXX

        elif self.state == STATE_COLLECT:

            response_body = json.load(response.body)

            #
            # We store each iteration of the test as a separate row of
            # the backend. We also add a whole test timestamp, to allow
            # one to understand which row belong to the same test.
            #
            whole_test_timestamp = utils.timestamp()

            for index, elem in enumerate(self.measurements):
                elem["clnt_schema_version"] = 3
                elem["whole_test_timestamp"] = whole_test_timestamp
                if index < len(response_body):
                    elem["srvr_data"] = response_body[index]
                BACKEND.store_generic("dash", elem)

            stream.close()

        else:
            raise RuntimeError("dash: internal error")

    #
    # Note: get_auth() and append_result() are
    # called by self.client.
    #

    def get_auth(self):
        """ Return the authorization token """
        return self.authorization

    def append_result(self, data):
        """ Append data to client-side results """
        self.measurements.append(data)

    def test_complete(self):
        """ Invoked when the test is complete """

        stream = self.stream

        logging.info("dash: collect... in progress")
        STATE.update("collect")
        self.state = STATE_COLLECT

        body = json.dumps(self.measurements)

        request = Message()
        request.compose(method="POST", pathquery="/collect/dash",
          body=body, mimetype="application/json", host=self.host_header)

        request["authorization"] = self.authorization

        stream.set_timeout(15)

        stream.send_request(request)

    def connection_lost(self, stream):
        logging.info("dash: negotiate connection closed: test done")
        NOTIFIER.publish("testdone")
        self.client = None
        self.stream = None

    def connection_failed(self, connector, exception):
        logging.info("dash: connect() failed: test done")
        NOTIFIER.publish("testdone")
