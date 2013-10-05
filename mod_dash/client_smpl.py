# mod_dash/client_smpl.py

#
# Copyright (c) 2013 Antonio Servetti <antonio.servetti@polito.it>
#
# Copyright (c) 2010-2013
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

""" MPEG DASH client """

import bisect
import logging
import os

from neubot.http.client import ClientHTTP
from neubot.http.message import Message

from neubot.state import STATE

from neubot import utils
from neubot import utils_net
from neubot import utils_version

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
]

#
# We want the download to run for about this number of seconds,
# plus one RTT, plus the queuing delay.
#
DASH_SECONDS = 2

#
# We iterate the DASH download the following number of times,
# and we possibly variate the download rate each time.
#
DASH_MAX_ITERATION = 15

class DASHClientSmpl(ClientHTTP):
    """ The MPEG DASH client """

    def __init__(self, poller, parent):
        ClientHTTP.__init__(self, poller)
        self.parent = parent

        STATE.update("test_latency", "---", publish=False)
        STATE.update("test_download", "---", publish=False)
        STATE.update("test_upload", "---", publish=False)
        STATE.update("test_name", "dash")

        self.iteration = 0
        self.saved_ticks = 0.0
        self.saved_cnt = 0
        self.saved_times = 0
        self.rate_index = 0

    def connect(self, endpoint, count=1):
        if count != 1:
            raise RuntimeError("dash: invalid count")
        logging.debug("dash: connect() to: %s",
          utils_net.format_epnt(endpoint))
        ClientHTTP.connect(self, endpoint, count)

    def connect_uri(self, uri=None, count=None):
        # Note: to discourage people from using connect_uri()
        raise RuntimeError("dash: please, use connect()")

    def connection_ready(self, stream):
        """ Invoked when the connection is ready """

        STATE.update("test_latency", utils.time_formatter(self.rtts[0]))

        #
        # We start with index equal to zero (i.e., the lowest MPEG DASH
        # rate) and we update the index after each download.
        #
        # We request a number of bytes which shall keep the download
        # time under DASH_SECONDS seconds plus one round-trip time
        # plus the queuing delay at the bottleneck.
        #

        rate = DASH_RATES[self.rate_index]
        count = ((rate * 1000) / 8) * DASH_SECONDS
        uri = "/dash/download/%d" % count

        logging.debug("dash: connection ready - rate %d Kbit/s", rate)

        request = Message()
        request.compose(method="GET", pathquery=uri,
                        host=self.host_header)
        if self.parent:
            auth = self.parent.get_auth()
            logging.debug("dash: authorization - %s", auth)
            request["authorization"] = auth

        self.saved_ticks = utils.ticks()
        self.saved_cnt = stream.bytes_recv_tot
        self.saved_times = os.times()[:2]

        response = Message()

        # Receive and discard the body
        response.body.write = lambda piece: None

        logging.debug("dash: send request - ticks %f, bytes %d, times %s",
          self.saved_ticks, self.saved_cnt, self.saved_times)

        stream.send_request(request, response)

    def got_response(self, stream, request, response):
        """ Invoked when we receive the response from the server """

        if response.code != "200":
            logging.warning("dash: invalid response: %s", response.code)
            stream.close()
            return

        new_ticks = utils.ticks()
        new_bytes = stream.bytes_recv_tot
        new_times = os.times()[:2]

        logging.debug("dash: got response - ticks %f, bytes %d, times %s",
          new_ticks, new_bytes, new_times)

        elapsed = new_ticks - self.saved_ticks
        received = new_bytes - self.saved_cnt
        delta_user_time = new_times[0] - self.saved_times[0]
        delta_sys_time = new_times[1] - self.saved_times[1]

        if elapsed < 0:
            raise RuntimeError("dash: clock going backwards")

        logging.debug("dash: got response - elaps %f, rcvd %d, user %f, sys %f",
          elapsed, received, delta_user_time, delta_sys_time)

        if self.parent:
            result = {
                      "connect_time": self.rtts[0],
                      "delta_user_time": delta_user_time,
                      "delta_sys_time": delta_sys_time,
                      "elapsed": elapsed,
                      "internal_address": stream.myname[0],
                      "iteration": self.iteration,
                      "rate": DASH_RATES[self.rate_index],
                      "rate_index": self.rate_index,
                      "real_address": self.parent.real_address,
                      "remote_address": stream.peername[0],
                      "received": received,
                      "timestamp": utils.timestamp(),
                      "uuid": self.conf.get("uuid"),
                      "version": utils_version.NUMERIC_VERSION,
                     }
            self.parent.append_result(result)

        #
        # We perform at most DASH_MAX_ITERATION iterations, to keep
        # the total elapsed test time under control.
        #

        self.iteration += 1
        if self.iteration >= DASH_MAX_ITERATION:
            logging.debug("dash: done all iteration")
            stream.close()
            return

        #
        # Note: when the rate is faster than the maximum rate,
        # the bisect point is one past the last element, and
        # thus we must patch the index to avoid an IndexError.
        #

        speed = received / elapsed
        speed_kilobit = (speed * 8) / 1000
        self.rate_index = bisect.bisect_left(DASH_RATES, speed_kilobit)
        if self.rate_index >= len(DASH_RATES):
            self.rate_index = len(DASH_RATES) - 1

        STATE.update("test_download", utils.speed_formatter(speed))
        logging.debug("dash: speed - %f Kbit/s", speed_kilobit)

        self.connection_ready(stream)

    def connection_failed(self, connector, exception):
        logging.warning("dash: connection failed: %s", exception)
        if self.parent:
            self.parent.test_complete()

    def connection_lost(self, stream):
        if self.iteration < DASH_MAX_ITERATION:
            logging.warning("dash: connection closed prematurely")
        if self.parent:
            self.parent.test_complete()
