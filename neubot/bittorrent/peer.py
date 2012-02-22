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

'''
 This file tries to emulate the behavior of a
 BitTorrent peer to the extent that is required
 by Neubot's purpose.
'''

import random

from neubot.bittorrent.bitfield import Bitfield
from neubot.bittorrent.bitfield import make_bitfield
from neubot.bittorrent.sched import sched_req
from neubot.bittorrent.stream import StreamBitTorrent
from neubot.net.stream import StreamHandler

from neubot.bittorrent import estimate
from neubot.log import LOG
from neubot.state import STATE

from neubot import utils

# Constants
from neubot.bittorrent.config import NUMPIECES
from neubot.bittorrent.config import PIECE_LEN
from neubot.bittorrent.config import WATCHDOG

LO_THRESH = 3
MAX_REPEAT = 7
TARGET = 5

# States of the PeerNeubot object
STATES = (INITIAL, SENT_INTERESTED, DOWNLOADING, UPLOADING,
          SENT_NOT_INTERESTED) = range(5)

#
# This class implements the test finite state
# machine and message exchange that are documented
# by <doc/bittorrent/peer.png>.
#
class PeerNeubot(StreamHandler):
    def __init__(self, poller):
        StreamHandler.__init__(self, poller)
        STATE.update("test", "bittorrent")
        self.connector_side = False
        self.saved_bytes = 0
        self.saved_ticks = 0
        self.inflight = 0
        self.dload_speed = 0
        self.repeat = MAX_REPEAT
        self.state = INITIAL
        self.infohash = None
        self.rtt = 0

    def configure(self, conf):
        StreamHandler.configure(self, conf)
        self.numpieces = conf["bittorrent.numpieces"]
        self.bitfield = make_bitfield(self.numpieces)
        self.peer_bitfield = make_bitfield(self.numpieces)
        self.my_id = conf["bittorrent.my_id"]
        self.target_bytes = conf["bittorrent.bytes.down"]
        self.make_sched()

    def make_sched(self):
        self.sched_req = sched_req(self.bitfield, self.peer_bitfield,
          self.target_bytes, self.conf["bittorrent.piece_len"],
          self.conf["bittorrent.piece_len"])

    def connect(self, endpoint, count=1):
        self.connector_side = True
        #
        # In Neubot the listener does not have an infohash
        # and handshakes, including connector infohash, after
        # it receives the connector handshake.
        #
        self.infohash = self.conf["bittorrent.infohash"]
        LOG.start("BitTorrent: connecting to %s" % str(endpoint))
        StreamHandler.connect(self, endpoint, count)

    #
    # Empty but here to remind hackers that the controlling
    # object must divert this function to its own function in
    # order to catch the case where we cannot connect to the
    # remote end.
    #
    def connection_failed(self, connector, exception):
        pass

    def connection_made(self, sock, rtt=0):
        if rtt:
            latency = utils.time_formatter(rtt)
            LOG.complete("done, %s" % latency)
            STATE.update("test_latency", latency)
            self.rtt = rtt
        stream = StreamBitTorrent(self.poller)
        if not self.connector_side:
            #
            # Note that we use self.__class__() because self
            # might be a subclass of PeerNeubot.
            #
            peer = self.__class__(self.poller)
            peer.configure(self.conf)
        else:
            peer = self
        stream.attach(peer, sock, peer.conf)
        stream.watchdog = self.conf["bittorrent.watchdog"]

    def connection_ready(self, stream):
        stream.send_bitfield(str(self.bitfield))
        LOG.start("BitTorrent: receiving bitfield")
        if self.connector_side:
            self.state = SENT_INTERESTED
            stream.send_interested()

    def got_bitfield(self, b):
        self.peer_bitfield = Bitfield(self.numpieces, b)
        LOG.complete()

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

        if begin + length > PIECE_LEN:
            raise RuntimeError("REQUEST too big")

        #
        # TODO Here we should use the random block
        # generator but before we do that we should
        # also make sure it does not slow down the
        # bittorrent test.
        #
        block = chr(random.randint(32, 126)) * length
        stream.send_piece(index, begin, block)

    def got_interested(self, stream):
        if self.connector_side and self.state != SENT_NOT_INTERESTED:
            raise RuntimeError("INTERESTED when state != SENT_NOT_INTERESTED")
        if not self.connector_side and self.state != INITIAL:
            raise RuntimeError("INTERESTED when state != INITIAL")
        LOG.start("BitTorrent: uploading")
        self.state = UPLOADING
        stream.send_unchoke()

    def got_not_interested(self, stream):
        if self.state != UPLOADING:
            raise RuntimeError("NOT_INTERESTED when state != UPLOADING")
        LOG.complete()
        if self.connector_side:
            self.complete(stream, self.dload_speed, self.rtt,
                          self.target_bytes)
            stream.close()
        else:
            self.state = SENT_INTERESTED
            stream.send_interested()

    # Download

    #
    # XXX Not so clean to panic on CHOKE however the test
    # does not use this message and we cannot simply ignore
    # it because it would violate the protocol.
    #
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
            LOG.start("BitTorrent: downloading %d bytes" % self.target_bytes)
            burst = self.sched_req.next()
            for index, begin, length in burst:
                stream.send_request(index, begin, length)
                self.inflight += 1

    def got_have(self, index):
        if self.state != UPLOADING:
            raise RuntimeError("HAVE when state != UPLOADING")
        self.peer_bitfield[index] = 1
        # We don't use HAVE messages at the moment
        LOG.warning("Ignoring unexpected HAVE message")

    #
    # Time to put another piece on the wire, assuming
    # that we can do that.  Note that we start measuring
    # after the first PIECE message: at that point we
    # can assume the pipeline to be full (note that this
    # holds iff bdp < initial-burst).
    # Note to self: when the connection is buffer limited
    # the TCP stack is very likely to miss fast retransmit
    # and recovery.  We cannot measure throughput in that
    # condition but the fact that TCP is more sensitive to
    # losses might be interesting as well.
    #
    def got_piece(self, stream, index, begin, block):
        if self.state != DOWNLOADING:
            raise RuntimeError("PIECE when state != DOWNLOADING")

        # Start measuring
        if not self.saved_ticks:
            self.saved_bytes = stream.bytes_recv_tot
            self.saved_ticks = utils.ticks()

        # Get next piece
        try:
            vector = self.sched_req.next()
        except StopIteration:
            vector = None

        if vector:
            # Send next piece
            index, begin, length = vector[0]
            stream.send_request(index, begin, length)

        else:
            #
            # No more pieces: Wait for the pipeline to empty
            #
            # TODO Check whether it's better to stop the measurement
            # when the pipeline starts emptying instead of when it
            # becomes empty (maybe it is reasonable to discard when
            # it fills and when it empties, isn't it?)
            #
            self.inflight -= 1
            if self.inflight == 0:
                xfered = stream.bytes_recv_tot - self.saved_bytes
                elapsed = utils.ticks() - self.saved_ticks
                speed = xfered/elapsed

                LOG.complete("%s" % utils.speed_formatter(speed))

                #
                # Make sure that next test would take about
                # TARGET secs, under current conditions.
                # We're a bit conservative when the elapsed
                # time is small because there is the risk of
                # overestimating the available bandwith.
                # TODO Don't start from scratch but use speedtest
                # estimate (maybe we need to divide it by two
                # but I'm not sure at the moment).
                #
                if elapsed >= LO_THRESH/3:
                    self.target_bytes = int(self.target_bytes * TARGET/elapsed)
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
                    self.state = SENT_NOT_INTERESTED
                    stream.send_not_interested()
                    if not self.connector_side:
                        self.complete(stream, self.dload_speed, self.rtt,
                                      self.target_bytes)
                    else:
                        download = utils.speed_formatter(self.dload_speed)
                        STATE.update("test_download", download)
                else:
                    self.saved_ticks = 0
                    self.make_sched()
                    self.state = SENT_INTERESTED        #XXX
                    self.got_unchoke(stream)

            elif self.inflight < 0:
                raise RuntimeError("Inflight became negative")

    def complete(self, stream, speed, rtt, target_bytes):
        pass
