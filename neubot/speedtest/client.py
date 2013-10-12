# neubot/speedtest/client.py

#
# Copyright (c) 2010-2012 Simone Basso <bassosimone@gmail.com>,
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

import getopt
import StringIO
import collections
import sys
import logging
import os

from neubot.utils_random import RandomBody
from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.database import table_speedtest
from neubot.http.client import ClientHTTP
from neubot.http.message import Message
from neubot.net.poller import POLLER
from neubot.notify import NOTIFIER
from neubot.state import STATE
from neubot.speedtest.wrapper import SpeedtestCollect
from neubot.speedtest.wrapper import SpeedtestNegotiate_Response
from neubot import utils_version

from neubot.backend import BACKEND

from neubot import log
from neubot import marshal
from neubot import privacy
from neubot import utils

from neubot.bytegen_speedtest import BytegenSpeedtest
from neubot import runner_clnt

from neubot import utils_version

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

        #
        # With version 2, we do not send range header and the
        # server will understand that it needs to send us chunked
        # data for its TARGET number of seconds.
        #
        if self.conf['version'] == 1:
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

        #
        # With version 2, we upload bytes using chunked transfer
        # encoding for TARGET seconds.
        #
        if self.conf['version'] == 2:
            body = BytegenSpeedtest(TARGET)
            request.compose(method='POST', chunked=body,
              pathquery='/speedtest/upload', host=self.host_header)
            request['authorization'] = self.conf[
              'speedtest.client.authorization']
            stream.send_request(request)
            self.ticks[stream] = utils.ticks()
            self.bytes[stream] = stream.bytes_sent_tot
            return

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
        #
        # Note: the negotiation of the other tests uses POST and includes a
        # possibly-empty body (see, e.g., mod_dash). Here it is fine, instead,
        # to have GET plus an empty body, because the speedtest is still
        # based on the legacy "/speedtest/negotiate" negotiator.
        #
        request.compose(method="GET", pathquery="/speedtest/negotiate",
          host=self.host_header)
        request["authorization"] = self.conf.get(
          "speedtest.client.authorization", "")
        stream.send_request(request)

    def got_response(self, stream, request, response):
        m = marshal.unmarshal_object(response.body.read(), "text/xml",
                                     SpeedtestNegotiate_Response)
        self.conf["speedtest.client.authorization"] = m.authorization
        self.conf["speedtest.client.public_address"] = m.publicAddress
        self.conf["speedtest.client.unchoked"] = utils.intify(m.unchoked)
        if m.queuePos:
            self.conf["speedtest.client.queuepos"] = m.queuePos

### Glue result class and dictionary ###

#
# FIXME The following function glues the speedtest code and
# the database code.  The speedtest code passes downstream a
# an object with the following problems:
#
# 1. the timestamp _might_ be a floating because old
#    neubot clients have this bug;
#
def obj_to_dict(obj):
    ''' Hack to convert speedtest result object into a
        dictionary. '''
    dictionary = {
        "uuid": obj.client,
        "timestamp": int(float(obj.timestamp)),         #XXX
        "internal_address": obj.internalAddress,
        "real_address": obj.realAddress,
        "remote_address": obj.remoteAddress,
        "connect_time": obj.connectTime,
        "latency": obj.latency,
        "download_speed": obj.downloadSpeed,
        "upload_speed": obj.uploadSpeed,
        "privacy_informed": obj.privacy_informed,
        "privacy_can_collect": obj.privacy_can_collect,
        "privacy_can_publish": obj.privacy_can_share,   #XXX
        "platform": obj.platform,
        "neubot_version": obj.neubot_version,

        # Test version (added Neubot 0.4.12)
        "test_version": obj.testVersion,
    }
    return dictionary

def insertxxx(connection, obj, commit=True, override_timestamp=True):
    ''' Hack to insert a result object into speedtest table,
        converting it into a dictionary. '''
    table_speedtest.insert(connection, obj_to_dict(obj), commit,
                           override_timestamp)

### Glue result class and dictionary ###

class ClientCollect(ClientHTTP):
    def connection_ready(self, stream):
        m1 = SpeedtestCollect()
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
        m1.privacy_can_share = self.conf.get("privacy.can_publish", 0)  # XXX

        m1.neubot_version = utils_version.NUMERIC_VERSION
        m1.platform = sys.platform

        m1.connectTime = sum(self.rtts) / len(self.rtts)

        # Test version (added Neubot 0.4.12)
        m1.testVersion = CONFIG['speedtest_test_version']

        s = marshal.marshal_object(m1, "text/xml")
        stringio = StringIO.StringIO(s)

        #
        # Pass a dictionary because the function does not accept
        # anymore an object
        #
        if privacy.collect_allowed(m1.__dict__):
            if DATABASE.readonly:
                logging.warning('speedtest: readonly database')
            else:
                insertxxx(DATABASE.connection(), m1)

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
        STATE.update("test_latency", "---", publish=False)
        STATE.update("test_download", "---", publish=False)
        STATE.update("test_upload", "---", publish=False)
        STATE.update("test_progress", "0%", publish=False)
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
              "http://master.neubot.org/")
        if not count:
            count = self.conf.get("speedtest.client.nconn", 1)
        logging.info("* speedtest with %s", uri)
        ClientHTTP.connect_uri(self, uri, count)

    def connection_ready(self, stream):

        self.conf['version'] = CONFIG['speedtest_test_version']

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
                logging.error("* speedtest: %s", message)
            while self.streams:
                self.streams.popleft().close()
            self.child = None
            NOTIFIER.publish(TESTDONE)

    def got_response(self, stream, request, response):
        if self.finished:
            stream.close()
            return
        if response.code not in ("200", "206"):
            stream.close()
            self.cleanup("bad response code")
        else:
            try:
                self.child.got_response(stream, request, response)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.error('Exception', exc_info=1)
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
                logging.info("* speedtest: %s ... authorized to "
                  "take the test\n", self.state)
                self.state = "latency"
            elif "speedtest.client.queuepos" in self.conf:
                queuepos = self.conf["speedtest.client.queuepos"]
                logging.info("* speedtest: %s ... waiting in queue, "
                  "pos %s\n", self.state, queuepos)
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
                STATE.update("test_progress", "33%", publish=False)
                STATE.update("test_latency", utils.time_formatter(latency))
                logging.info("* speedtest: %s ...  done, %s\n", self.state,
                  utils.time_formatter(latency))
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
                      utils.speed_formatter(speed), publish=False)
                    logging.info("* speedtest: %s ...  done, %s\n", self.state,
                      utils.speed_formatter(speed))
                    if self.state == "download":
                        STATE.update("test_progress", "66%")
                        self.state = "upload"
                    else:
                        STATE.update("test_progress", "100%")
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
            logging.info("* speedtest: %s ... done\n", self.state)
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
                    STATE.update("test", "speedtest")
            else:
                STATE.update(self.state)
            logging.info("* speedtest: %s in progress...", self.state)
        elif self.state == "negotiate":
            logging.info("* speedtest: %s in progress...", self.state)

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
    "speedtest.client.uri": "http://master.neubot.org/",
    "speedtest.client.nconn": 1,
    "speedtest.client.latency_tries": 10,
})

def main(args):
    """ Main function """
    try:
        options, arguments = getopt.getopt(args[1:], '6A:fp:v')
    except getopt.error:
        sys.exit('usage: neubot speedtest [-6fv] [-A address] [-p port]')
    if arguments:
        sys.exit('usage: neubot speedtest [-6fv] [-A address] [-p port]')

    prefer_ipv6 = 0
    address = 'master.neubot.org'
    force = 0
    port = 8080
    noisy = 0
    for name, value in options:
        if name == '-6':
            prefer_ipv6 = 1
        elif name == '-A':
            address = value
        elif name == '-f':
            force = 1
        elif name == '-p':
            port = int(value)
        elif name == '-v':
            noisy = 1

    if os.path.isfile(DATABASE.path):
        DATABASE.connect()
        CONFIG.merge_database(DATABASE.connection())
    else:
        logging.warning('speedtest: database file is missing: %s',
                        DATABASE.path)
        BACKEND.use_backend('null')
    if noisy:
        log.set_verbose()

    conf = CONFIG.copy()
    conf["speedtest.client.uri"] = "http://%s:%d/" % (address, port)
    conf["prefer_ipv6"] = prefer_ipv6

    if not force:
        if runner_clnt.runner_client(conf["agent.api.address"],
                                     conf["agent.api.port"],
                                     CONFIG['verbose'],
                                     "speedtest"):
            sys.exit(0)
        logging.warning(
          'speedtest: failed to contact Neubot; is Neubot running?')
        sys.exit(1)

    logging.info('speedtest: run the test in the local process context...')
    client = ClientSpeedtest(POLLER)
    client.configure(conf)
    client.connect_uri()
    POLLER.loop()
