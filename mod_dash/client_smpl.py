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
import sys

from neubot.http.client import ClientHTTP
from neubot.http.message import Message

from neubot.state import STATE

from neubot import utils
from neubot import utils_net
from neubot import utils_version

#
# We want the download of a chunk to run for about this number of
# seconds, plus one RTT, plus the queuing delay.
#
DASH_SECONDS = 2

#
# We iterate the DASH download of a chunk for the following number of
# times, and we possibly variate the download rate each time.
#
DASH_MAX_ITERATION = 15

class DASHClientSmpl(ClientHTTP):
    """ The MPEG DASH client """

    #
    # As far as user experience is concerned, we want to perform a test
    # in which each chunk is downloaded in roughly DASH_SECONDS, plus one
    # round-trip delay, and hopefully with acceptable queueing delay.
    #

    def __init__(self, poller, parent, rates):
        ClientHTTP.__init__(self, poller)
        self.parent = parent
        self.rates = rates

        STATE.update("test_latency", "---", publish=False)
        STATE.update("test_download", "---", publish=False)
        STATE.update("test_upload", "N/A", publish=False)
        STATE.update("test_progress", "0%", publish=False)
        STATE.update("test_name", "dash", publish=False)
        STATE.update("test")

        self.iteration = 0
        self.rate_kbit = 0
        self.speed_kbit = 100
        self.saved_ticks = 0.0
        self.saved_cnt = 0
        self.saved_times = 0

    def connect(self, endpoint, count=1):
        if count != 1:
            raise RuntimeError("dash: invalid count")
        logging.info("dash: test with: %s", utils_net.format_epnt(endpoint))
        ClientHTTP.connect(self, endpoint, count)

    def connect_uri(self, uri=None, count=None):
        # Note: to discourage people from using connect_uri()
        raise RuntimeError("dash: please, use connect()")

    def connection_ready(self, stream):
        """ Invoked when the connection is ready """

        if self.iteration == 0:
            STATE.update("test_latency", utils.time_formatter(self.rtts[0]))
            logging.info("dash: latency %s", utils.time_formatter(self.rtts[0]))

        #
        # Pick the greatest rate in the vector that is smaller
        # than the latest piece rate (saved in speed_kbit).
        #
        # Note: we pick one minus the bisect point because we
        # want to use the closest smaller rate for the next
        # chunk of "video" that we download.
        #
        rate_index = bisect.bisect(self.rates, self.speed_kbit) - 1
        if rate_index < 0:
            rate_index = 0
        self.rate_kbit = self.rates[rate_index]

        count = ((self.rate_kbit * 1000) / 8) * DASH_SECONDS
        uri = "/dash/download/%d" % count

        logging.debug("dash: connection ready - rate %d Kbit/s",
                      self.rate_kbit)

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

        stream.set_timeout(10)

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
                      "elapsed_target": DASH_SECONDS,
                      "internal_address": stream.myname[0],
                      "iteration": self.iteration,
                      "platform": sys.platform,
                      "rate": self.rate_kbit,
                      "real_address": self.parent.real_address,
                      "received": received,
                      "remote_address": stream.peername[0],
                      "request_ticks": self.saved_ticks,
                      "timestamp": utils.timestamp(),
                      "uuid": self.conf.get("uuid"),
                      "version": utils_version.NUMERIC_VERSION,
                     }
            self.parent.append_result(result)

        self.iteration += 1

        #
        # TODO it would be nice to also STATE.update() with the dash
        # rate, but that change requires also some www changes.
        #

        STATE.update("test_progress", "%d%%" % ((100 * self.iteration)
          / DASH_MAX_ITERATION), publish=False)

        speed = received / elapsed
        self.speed_kbit = (speed * 8) / 1000

        STATE.update("test_download", utils.speed_formatter(speed))
        logging.info(
          "dash: [%2d/%d] rate: %6d Kbit/s, speed: %6d Kbit/s, elapsed: %.3f s",
          self.iteration, DASH_MAX_ITERATION, self.rate_kbit, self.speed_kbit,
          elapsed)

        if self.iteration >= DASH_MAX_ITERATION:
            logging.debug("dash: done all iteration")
            stream.close()
            return

        #
        # If we're adding too much delay, artificially reduce the
        # measured speed to let the bottleneck breathe.
        #
        if elapsed > DASH_SECONDS:
            rel_err = 1 - elapsed / DASH_SECONDS
            self.speed_kbit += rel_err * self.speed_kbit
            if self.speed_kbit < 0:
                self.speed_kbit = 100

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
