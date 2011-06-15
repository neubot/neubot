# neubot/bittorrent/peer.py

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

import random

from neubot.blocks import RandomBody
from neubot.bittorrent.bitfield import Bitfield
from neubot.bittorrent.bitfield import make_bitfield
from neubot.bittorrent.sched import sched_req
from neubot.bittorrent.stream import StreamBitTorrent
from neubot.bittorrent.stream import SMALLMESSAGE
from neubot.log import LOG
from neubot.net.stream import StreamHandler

from neubot import utils

NUMPIECES = 1<<20
PIECE_LEN = SMALLMESSAGE
PIPELINE = 1<<20
TARGET_BYTES = 64000

LO_THRESH = 5
MAX_REPEAT = 7
TARGET = 8

# States of the PeerNeubot object
STATES = [INITIAL, SENT_INTERESTED, DOWNLOADING, UPLOADING,
          SENT_NOT_INTERESTED] = range(5)

def random_bytes(n):
    return "".join([chr(random.randint(32, 126)) for _ in range(n)])

#
# This class implements the test finite state
# machine and message exchange that are documented
# in <doc/bittorrent/peer.png>.
#
class PeerNeubot(StreamHandler):
    def __init__(self, poller):
        StreamHandler.__init__(self, poller)
        self.connector_side = False
        self.saved_bytes = 0
        self.saved_ticks = 0
        self.inflight = 0
        self.dload_speed = 0
        self.repeat = MAX_REPEAT
        self.state = INITIAL
        self.rtt = 0
        self.setup({})

    def configure(self, conf, measurer=None):
        StreamHandler.configure(self, conf, measurer)
        self.setup(conf)

    def setup(self, conf):
        self.numpieces = int(conf.get("bittorrent.numpieces", NUMPIECES))
        self.bitfield = make_bitfield(self.numpieces)
        self.peer_bitfield = make_bitfield(self.numpieces)
        self.infohash = conf.get("bittorrent.infohash", random_bytes(20))
        self.my_id = conf.get("bittorrent.my_id", random_bytes(20))
        self.target_bytes = int(self.conf.get("bittorrent.target_bytes",
                              TARGET_BYTES))
        self.make_sched()

    def make_sched(self):
        self.sched_req = sched_req(self.bitfield, self.peer_bitfield,
          self.target_bytes, int(self.conf.get("bittorrent.piece_len",
          PIECE_LEN)), PIPELINE)

    def connection_ready(self, stream):
        stream.send_bitfield(str(self.bitfield))
        if self.connector_side:
            self.state = SENT_INTERESTED
            stream.send_interested()

    def connect(self, endpoint, count=1):
        self.connector_side = True
        StreamHandler.connect(self, endpoint, count)

    #
    # Always handle the BitTorrent connection using a
    # new object, so we can use the same code both for
    # the connector and the listener.
    # Note that we use self.__class__() because self
    # might be a subclass of PeerNeubot.
    #
    def connection_made(self, sock, rtt=0):
        if rtt:
            LOG.info("BitTorrent: latency: %s" % utils.time_formatter(rtt))
            self.rtt = rtt
        stream = StreamBitTorrent(self.poller)
        peer = self.__class__(self.poller)
        peer.configure(self.conf, self.measurer)
        peer.connector_side = self.connector_side               #XXX
        stream.attach(peer, sock, peer.conf, peer.measurer)

    def got_bitfield(self, b):
        self.peer_bitfield = Bitfield(self.numpieces, b)

    # Upload

    #
    # XXX As suggested by BEP0003, we should keep blocks into
    # an application level queue and just pipe a few of them
    # into the socket buffer, so we can abort the upload in a
    # graceful way.
    #
    def got_request(self, stream, index, begin, length):
        if self.state != UPLOADING:
            raise RuntimeError("REQUEST when state != UPLOADING")
        if length <= SMALLMESSAGE:
            block = chr(random.randint(32, 126)) * length
        else:
            block = RandomBody(length)
        stream.send_piece(index, begin, block)

    def got_interested(self, stream):
        if self.connector_side and self.state != SENT_NOT_INTERESTED:
            raise RuntimeError("INTERESTED when state != SENT_NOT_INTERESTED")
        if not self.connector_side and self.state != INITIAL:
            raise RuntimeError("INTERESTED when state != INITIAL")
        self.state = UPLOADING
        stream.send_unchoke()

    def got_not_interested(self, stream):
        if self.state != UPLOADING:
            raise RuntimeError("NOT_INTERESTED when state != UPLOADING")
        if self.connector_side:
            LOG.info("BitTorrent: test complete")
            self.complete(self.dload_speed, self.rtt)
            stream.close()
        else:
            self.state = SENT_INTERESTED
            stream.send_interested()

    # Download

    def got_choke(self, stream):
        raise RuntimeError("Unexpected CHOKE message")

    #
    # When we're unchoked immediately pipeline a number
    # of requests and then put another request on the pipe
    # as soon as a piece arrives.  Note that the pipelining
    # is automagically done by the scheduler generator.
    # The idea of pipelining is that of filling with many
    # messages the space between us and the peer to do
    # something that approxymates a continuous download.
    #
    def got_unchoke(self, stream):
        if self.state != SENT_INTERESTED:
            raise RuntimeError("UNCHOKE when state != SENT_INTERESTED")
        else:
            self.state = DOWNLOADING
            LOG.info("BitTorrent: using %d bytes" % self.target_bytes)
            burst = next(self.sched_req)
            for index, begin, length in burst:
                stream.send_request(index, begin, length)
                self.inflight += 1

    # We don't use HAVE messages at the moment
    def got_have(self, index):
        if self.state != UPLOADING:
            raise RuntimeError("HAVE when state != UPLOADING")
        self.peer_bitfield[index] = 1

    def got_piece(self, stream, index, begin, block):
        self.piece_start(stream, index, begin, "")
        self.piece_part(stream, index, begin, block)
        self.piece_end(stream, index, begin)

    def piece_start(self, stream, index, begin, block):
        pass
    def piece_part(self, stream, index, begin, block):
        pass

    #
    # Time to put another piece on the wire, assuming
    # that we can do that.  Note that we start measuring
    # after the first PIECE message: at that point we
    # can assume the pipeline to be full (note that this
    # holds iff bdp < PIPELINE).
    #
    def piece_end(self, stream, index, begin):
        if self.state != DOWNLOADING:
            raise RuntimeError("PIECE when state != DOWNLOADING")

        # Start measuring
        if not self.saved_ticks:
            self.saved_bytes = stream.bytes_recv_tot
            self.saved_ticks = utils.ticks()

        # Get next piece
        try:
            vector = next(self.sched_req)
        except StopIteration:
            vector = None

        if vector:
            # Send next piece
            index, begin, length = vector[0]
            stream.send_request(index, begin, length)

        else:
            # No more pieces: Wait for the pipeline to empty
            self.inflight -= 1
            if self.inflight == 0:
                xfered = stream.bytes_recv_tot - self.saved_bytes
                elapsed = utils.ticks() - self.saved_ticks
                speed = xfered/elapsed

                LOG.info("BitTorrent: download speed: %s" %
                  utils.speed_formatter(speed))
                LOG.info("BitTorrent: measurement time: %s" %
                  utils.time_formatter(elapsed))

                #
                # Make sure that next test would take about
                # TARGET secs, under current conditions.
                # But, multiply by two below a given threshold
                # because we don't want to overestimate the
                # achievable bandwidth.
                # TODO If we're the connector, store somewhere
                # the target_bytes so we can reuse it later.
                # TODO Don't start from scratch but use speedtest
                # estimate, maybe /2.
                #
                if elapsed > LO_THRESH/3:
                    self.target_bytes *= TARGET/elapsed
                else:
                    self.target_bytes *= 2

                #
                # The stopping rule is when the test has run
                # for more than LO_THRESH seconds or after some
                # number of runs (just to be sure that we can
                # not run forever due to unexpected network
                # conditions).
                #
                self.repeat -= 1
                if elapsed > LO_THRESH or self.repeat <= 0:
                    self.dload_speed = speed
                    LOG.info("BitTorrent: my side complete")
                    self.state = SENT_NOT_INTERESTED
                    stream.send_not_interested()
                    if not self.connector_side:
                        LOG.info("BitTorrent: test complete")
                        self.complete(self.dload_speed, self.rtt)
                else:
                    self.saved_ticks = 0
                    self.make_sched()
                    self.state = SENT_INTERESTED        #XXX
                    self.got_unchoke(stream)

            elif self.inflight < 0:
                raise RuntimeError("Inflight became negative")

    def complete(self, speed, rtt):
        pass
