# neubot/speedtest/client.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

import StringIO
import collections
import sys

from neubot.utils.blocks import RandomBody
from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.database import table_speedtest
from neubot.http.client import ClientHTTP
from neubot.http.message import Message
from neubot.log import LOG
from neubot.net.poller import POLLER
from neubot.notify import NOTIFIER
from neubot.state import STATE
from neubot.speedtest import compat
from neubot.utils.version import LibVersion

from neubot.main import common
from neubot import marshal
from neubot import privacy
from neubot import utils

TESTDONE = "testdone" #TODO: use directly the string instead

ESTIMATE = {
    "download": 64000,
    "upload": 64000,
}
LO_THRESH = 3
TARGET = 5

class ClientLatency(ClientHTTP):
    def __init__(self, poller):
        ClientHTTP.__init__(self, poller)
        self.ticks = {}

    def connection_ready(self, stream):
        request = Message()
        request.compose(method="HEAD", pathquery="/speedtest/latency",
          host=self.host_header)
        request["authorization"] = self.conf.get(
          "speedtest.client.authorization", "")
        self.ticks[stream] = utils.ticks()
        stream.send_request(request)

    def got_response(self, stream, request, response):
        ticks = utils.ticks() - self.ticks[stream]
        self.conf.setdefault("speedtest.client.latency",
          []).append(ticks)

class ClientDownload(ClientHTTP):
    def __init__(self, poller):
        ClientHTTP.__init__(self, poller)
        self.ticks = {}
        self.bytes = {}

    def connection_ready(self, stream):
        request = Message()
        request.compose(method="GET", pathquery="/speedtest/download",
          host=self.host_header)
        request["range"] = "bytes=0-%d" % ESTIMATE['download']
        request["authorization"] = self.conf.get(
          "speedtest.client.authorization", "")
        self.ticks[stream] = utils.ticks()
        self.bytes[stream] = stream.bytes_recv_tot
        response = Message()
        response.body.write = lambda piece: None
        stream.send_request(request, response)

    def got_response(self, stream, request, response):
        total = stream.bytes_recv_tot - self.bytes[stream]
        self.conf.setdefault("speedtest.client.download",
          []).append((self.ticks[stream], utils.ticks(), total))

class ClientUpload(ClientHTTP):
    def __init__(self, poller):
        ClientHTTP.__init__(self, poller)
        self.ticks = {}
        self.bytes = {}

    def connection_ready(self, stream):
        request = Message()
        request.compose(method="POST", body=RandomBody(ESTIMATE["upload"]),
          pathquery="/speedtest/upload", host=self.host_header)
        request["authorization"] = self.conf.get(
          "speedtest.client.authorization", "")
        self.ticks[stream] = utils.ticks()
        self.bytes[stream] = stream.bytes_sent_tot
        stream.send_request(request)

    def got_response(self, stream, request, response):
        total = stream.bytes_sent_tot - self.bytes[stream]
        self.conf.setdefault("speedtest.client.upload",
          []).append((self.ticks[stream], utils.ticks(), total))

class ClientNegotiate(ClientHTTP):
    def connection_ready(self, stream):
        request = Message()
        request.compose(method="GET", pathquery="/speedtest/negotiate",
          host=self.host_header)
        request["authorization"] = self.conf.get(
          "speedtest.client.authorization", "")
        stream.send_request(request)

    def got_response(self, stream, request, response):
        m = marshal.unmarshal_object(response.body.read(), "text/xml",
                                     compat.SpeedtestNegotiate_Response)
        self.conf["speedtest.client.authorization"] = m.authorization
        self.conf["speedtest.client.public_address"] = m.publicAddress
        self.conf["speedtest.client.unchoked"] = utils.intify(m.unchoked)
        if m.queuePos:
            self.conf["speedtest.client.queuepos"] = m.queuePos

class ClientCollect(ClientHTTP):
    def connection_ready(self, stream):
        m1 = compat.SpeedtestCollect()
        m1.client = self.conf.get("uuid", "")
        m1.timestamp = utils.timestamp()
        m1.internalAddress = stream.myname[0]
        m1.realAddress = self.conf.get("speedtest.client.public_address", "")
        m1.remoteAddress = stream.peername[0]

        m1.latency = self.conf.get("speedtest.client.latency", 0.0)
        m1.downloadSpeed = self.conf.get("speedtest.client.download", 0.0)
        m1.uploadSpeed = self.conf.get("speedtest.client.upload", 0.0)

        m1.privacy_informed = self.conf.get("privacy.informed", 0)
        m1.privacy_can_collect = self.conf.get("privacy.can_collect", 0)
        m1.privacy_can_share = self.conf.get("privacy.can_share", 0)

        m1.neubot_version = LibVersion.to_numeric("0.4.3")
        m1.platform = sys.platform

        m1.connectTime = sum(self.rtts) / len(self.rtts)

        s = marshal.marshal_object(m1, "text/xml")
        stringio = StringIO.StringIO(s)

        if privacy.collect_allowed(m1):
            table_speedtest.insertxxx(DATABASE.connection(), m1)

        request = Message()
        request.compose(method="POST", pathquery="/speedtest/collect",
                        body=stringio, mimetype="application/xml",
                        host=self.host_header)
        request["authorization"] = self.conf.get(
          "speedtest.client.authorization", "")

        stream.send_request(request)

#
# History of our position in queue, useful to ensure that
# the server-side queueing algorithm works well.
# The general idea is to reset the queue at the beginning of
# a new test and then append the queue position until we're
# authorized to take the test.
# We export this history via /api/debug, so it sneaks in when
# users send us bug reports et similia.
#
QUEUE_HISTORY = []

class ClientSpeedtest(ClientHTTP):
    def __init__(self, poller):
        ClientHTTP.__init__(self, poller)
        STATE.update("test_name", "speedtest")
        self.child = None
        self.streams = collections.deque()
        self.finished = False
        self.state = None

    def configure(self, conf):
        ClientHTTP.configure(self, conf)

    def connect_uri(self, uri=None, count=None):
        if not uri:
            uri = self.conf.get("speedtest.client.uri",
              "http://neubot.blupixel.net/")
        if not count:
            count = self.conf.get("speedtest.client.nconn", 1)
        LOG.info("* speedtest with %s" % uri)
        ClientHTTP.connect_uri(self, uri, count)

    def connection_ready(self, stream):
        self.streams.append(stream)
        if len(self.streams) == self.conf.get("speedtest.client.nconn", 1):
            self.update()

    #
    # When some sockets successfully connect and others do not,
    # the code in net/stream.py should close all the open sockets.
    # So we don't need to do gymnastics here.
    #
    def connection_failed(self, connector, exception):
        self.cleanup(message="connection failed")

    def connection_lost(self, stream):
        self.cleanup(message="connection lost")

    #
    # Here we close the idle sockets and we assume in-use
    # ones are closed either by got_response() or by the
    # remote HTTP server.
    #
    def cleanup(self, message=""):
        if not self.finished:
            self.finished = True
            if message:
                LOG.error("* speedtest: %s" % message)
            while self.streams:
                self.streams.popleft().close()
            self.child = None
            NOTIFIER.publish(TESTDONE)

    def got_response(self, stream, request, response):
        if self.finished:
            stream.close()
            return
        LOG.progress()
        if response.code not in ("200", "206"):
            stream.close()
            self.cleanup("bad response code")
        else:
            try:
                self.child.got_response(stream, request, response)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                LOG.exception()
                stream.close()
                self.cleanup("unexpected exception")
            else:
                self.streams.append(stream)
                self.update()

    def update(self):
        if self.finished:
            return

        #
        # Decide whether we can transition to the next phase of
        # the speedtest or not.  Fall through to next request if
        # needed, or return to the caller and rewind the stack.
        #

        ostate = self.state

        if not self.state:
            self.state = "negotiate"
            del QUEUE_HISTORY[:]

        elif self.state == "negotiate":
            if self.conf.get("speedtest.client.unchoked", False):
                LOG.complete("authorized to take the test\n")
                self.state = "latency"
            elif "speedtest.client.queuepos" in self.conf:
                queuepos = self.conf["speedtest.client.queuepos"]
                LOG.complete("waiting in queue, pos %s\n" % queuepos)
                STATE.update("negotiate", {"queue_pos": queuepos})
                QUEUE_HISTORY.append(queuepos)

        elif self.state == "latency":
            tries = self.conf.get("speedtest.client.latency_tries", 10)
            if tries == 0:
                # Calculate average latency
                latency = self.conf["speedtest.client.latency"]
                latency = sum(latency) / len(latency)
                self.conf["speedtest.client.latency"] = latency
                # Advertise the result
                STATE.update("test_latency", utils.time_formatter(latency))
                LOG.complete("done, %s\n" % utils.time_formatter(latency))
                self.state = "download"
            else:
                self.conf["speedtest.client.latency_tries"] = tries - 1

        elif self.state in ("download", "upload"):
            if len(self.streams) == self.conf.get("speedtest.client.nconn", 1):

                # Calculate average speed
                speed = self.conf["speedtest.client.%s" % self.state]
                elapsed = (max(map(lambda t: t[1], speed)) -
                  min(map(lambda t: t[0], speed)))
                speed = sum(map(lambda t: t[2], speed)) / elapsed
                LOG.progress(".[%s,%s]." % (utils.time_formatter(elapsed),
                       utils.speed_formatter(speed)))

                #
                # O(N) loopless adaptation to the channel w/ memory
                # TODO bittorrent/peer.py implements an enhanced version
                # of this algorithm, with a cap to the max number of
                # subsequent tests.  In addition to that, the bittorrent
                # code also anticipates the update of target_bytes.
                #
                if elapsed > LO_THRESH:
                    ESTIMATE[self.state] *= TARGET/elapsed
                    self.conf["speedtest.client.%s" % self.state] = speed
                    # Advertise
                    STATE.update("test_%s" % self.state,
                      utils.speed_formatter(speed))
                    LOG.complete("done, %s\n" % utils.speed_formatter(speed))
                    if self.state == "download":
                        self.state = "upload"
                    else:
                        self.state = "collect"
                elif elapsed > LO_THRESH/3:
                    del self.conf["speedtest.client.%s" % self.state]
                    ESTIMATE[self.state] *= TARGET/elapsed
                else:
                    del self.conf["speedtest.client.%s" % self.state]
                    ESTIMATE[self.state] *= 2

            else:
                # Wait for all pending requests to complete
                return

        elif self.state == "collect":
            LOG.complete()
            self.cleanup()
            return

        else:
            raise RuntimeError("Invalid state")

        #
        # Perform state transition and run the next phase of the
        # speedtest.  Not all phases need to employ all the connection
        # with the upstream server.
        #

        if self.state == "negotiate":
            ctor, justone = ClientNegotiate, True
        elif self.state == "latency":
            ctor, justone = ClientLatency, True
        elif self.state == "download":
            ctor, justone = ClientDownload, False
        elif self.state == "upload":
            ctor, justone = ClientUpload, False
        elif self.state == "collect":
            ctor, justone = ClientCollect, True
        else:
            raise RuntimeError("Invalid state")

        if ostate != self.state:
            self.child = ctor(self.poller)
            self.child.configure(self.conf)
            self.child.host_header = self.host_header
            if self.state not in ("negotiate", "collect"):
                if ostate == "negotiate" and self.state == "latency":
                    STATE.update("test_latency", "---", publish=False)
                    STATE.update("test_download", "---", publish=False)
                    STATE.update("test_upload", "---", publish=False)
                    STATE.update("test", "speedtest")
            else:
                STATE.update(self.state)
            LOG.start("* speedtest: %s" % self.state)
        elif self.state == "negotiate":
            LOG.start("* speedtest: %s" % self.state)

        while self.streams:
            #
            # Override child Time-To-Connect (TTC) with our TTC
            # so for the child it's like it really performed the
            # connect(), not us.
            #
            self.child.rtts = self.rtts
            self.child.connection_ready(self.streams.popleft())
            if justone:
                break

CONFIG.register_defaults({
    "speedtest.client.uri": "http://neubot.blupixel.net/",
    "speedtest.client.nconn": 1,
    "speedtest.client.latency_tries": 10,
})

def main(args):

    CONFIG.register_descriptions({
        "speedtest.client.uri": "Base URI to connect to",
        "speedtest.client.nconn": "Number of concurrent connections to use",
        "speedtest.client.latency_tries": "Number of latency measurements",
    })

    common.main("speedtest.client", "Speedtest client", args)
    conf = CONFIG.copy()
    client = ClientSpeedtest(POLLER)
    client.configure(conf)
    client.connect_uri()
    POLLER.loop()
