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
import logging
import getopt
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.bittorrent.bitfield import Bitfield
from neubot.bittorrent.bitfield import make_bitfield
from neubot.bittorrent.btsched import sched_req
from neubot.bittorrent.stream import StreamBitTorrent
from neubot.net.poller import POLLER
from neubot.net.stream import StreamHandler

from neubot.bittorrent import config
from neubot.config import CONFIG
from neubot.state import STATE

from neubot import utils
from neubot import utils_net
from neubot import utils_rc

# Constants
from neubot.bittorrent.config import PIECE_LEN

LO_THRESH = 3
MAX_REPEAT = 7
TARGET = 5

# States of the PeerNeubot object
STATES = (INITIAL, SENT_INTERESTED, DOWNLOADING, UPLOADING,
          SENT_NOT_INTERESTED, WAIT_REQUEST, WAIT_NOT_INTERESTED) = range(7)

#
# This class implements the test finite state
# machine and message exchange that are documented
# by <doc/neubot/bittorrent/peer.png>.
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
        self.version = 1
        self.begin_upload = 0.0

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
        logging.info("BitTorrent: connecting to %s in progress...",
          str(endpoint))
        StreamHandler.connect(self, endpoint, count)

    #
    # Empty but here to remind hackers that the controlling
    # object must divert this function to its own function in
    # order to catch the case where we cannot connect to the
    # remote end.
    #
    def connection_failed(self, connector, exception):
        pass

    def connection_made(self, sock, endpoint, rtt):
        if rtt:
            latency = utils.time_formatter(rtt)
            logging.info("BitTorrent: connecting to %s ... done, %s",
              str(utils_net.getpeername(sock)), latency)
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
            # Inherit version
            peer.version = self.version
        else:
            peer = self
        stream.attach(peer, sock, peer.conf)
        stream.watchdog = self.conf["bittorrent.watchdog"]

    def connection_ready(self, stream):
        stream.send_bitfield(str(self.bitfield))
        logging.debug('BitTorrent: test version %d', self.version)
        logging.info("BitTorrent: receiving bitfield in progress...")
        if self.connector_side:
            self.state = SENT_INTERESTED
            stream.send_interested()

    def got_bitfield(self, bitfield):
        self.peer_bitfield = Bitfield(self.numpieces, bitfield)
        logging.info("BitTorrent: receiving bitfield ... done")

    # Upload

    #
    # BEP0003 suggests to keep blocks into an application
    # level queue and just pipe few blocks into the socket
    # buffer, allowing for graceful abort.
    #
    def got_request(self, stream, index, begin, length):

        #
        # Start actual uploading when we receive the first REQUEST.
        # When the upload is over and we are waiting for NOT_INTERESTED
        # we ignore incoming REQUESTs.  Because they have "certainly"
        # been sent before the peer received our NOT_INTERESTED.
        #
        if self.version >= 2:
            if self.state == WAIT_REQUEST:
                self.begin_upload = utils.ticks()
                self.state = UPLOADING
                if self.version == 2:
                    # send_complete() kickstarts the uploader
                    self.send_complete(stream)
                    return
            elif self.state == WAIT_NOT_INTERESTED:
                return

        if self.state != UPLOADING:
            raise RuntimeError("REQUEST when state != UPLOADING")

        if begin + length > PIECE_LEN:
            raise RuntimeError("REQUEST too big")

        #
        # The rule that we send a PIECE each time we get a REQUEST is
        # not valid anymore, pieces go on the wire when the send queue
        # becomes empty.
        #
        if self.version == 2:
            return

        #
        # TODO Here we should use the random block
        # generator but before we do that we should
        # also make sure it does not slow down the
        # bittorrent test.
        #
        block = chr(random.randint(32, 126)) * length
        stream.send_piece(index, begin, block)

    def send_complete(self, stream):
        ''' Invoked when the send queue is empty '''

        if self.version >= 2 and self.state == UPLOADING:

            #
            # The sender stops sending when the upload has run for
            # enough time, notifies peer with CHOKE and waits for
            # NOT_INTERESTED.
            #
            diff = utils.ticks() - self.begin_upload
            if diff > TARGET:
                self.state = WAIT_NOT_INTERESTED
                stream.send_choke()
                return

            if self.version == 3:
                return

            #
            # TODO Here we should use the random block
            # generator but before we do that we should
            # also make sure it does not slow down the
            # bittorrent test.
            #
            block = chr(random.randint(32, 126)) * PIECE_LEN
            index = random.randrange(self.numpieces)
            stream.send_piece(index, 0, block)

    def got_interested(self, stream):
        if self.connector_side and self.state != SENT_NOT_INTERESTED:
            raise RuntimeError("INTERESTED when state != SENT_NOT_INTERESTED")
        if not self.connector_side and self.state != INITIAL:
            raise RuntimeError("INTERESTED when state != INITIAL")
        logging.info("BitTorrent: uploading in progress...")

        #
        # We don't start uploading until we receive
        # the first REQUEST from the peer.
        #
        if self.version >= 2:
            self.state = WAIT_REQUEST
            stream.send_unchoke()
            return

        self.state = UPLOADING
        stream.send_unchoke()

    def got_not_interested(self, stream):

        if self.state != UPLOADING and self.version == 1:
            raise RuntimeError("NOT_INTERESTED when state != UPLOADING")

        #
        # It's the sender that decides when it has sent
        # for enough time and enters WAIT_NOT_INTERESTED.
        #
        if self.state != WAIT_NOT_INTERESTED and self.version >= 2:
            raise RuntimeError("NOT_INTERESTED when state "
                               "!= WAIT_NOT_INTERESTED")

        logging.info("BitTorrent: uploading ... done")

        if self.connector_side:
            self.complete(stream, self.dload_speed, self.rtt,
                          self.target_bytes)
            stream.close()
        else:
            self.state = SENT_INTERESTED
            stream.send_interested()

    # Download

    def got_choke(self, stream):

        #
        # The download terminates when we recv CHOKE.
        # The code below is adapted from version 1
        # code in got_piece().
        #
        if self.version >= 2:
            logging.info('BitTorrent: download ... done')

            # Calculate speed
            xfered = stream.bytes_recv_tot - self.saved_bytes
            elapsed = utils.ticks() - self.saved_ticks
            self.dload_speed = xfered/elapsed

            # Properly terminate download
            self.state = SENT_NOT_INTERESTED
            stream.send_not_interested()

            download = utils.speed_formatter(self.dload_speed)
            logging.info('BitTorrent: download speed: %s', download)

            # To next state
            if not self.connector_side:
                self.complete(stream, self.dload_speed, self.rtt,
                              self.target_bytes)
            else:
                STATE.update("test_download", download)

            # We MUST NOT fallthru
            return

        #
        # We don't implement CHOKE and we cannot ignore it, since
        # that would violate the specification.  So we raise an
        # exception, which has the side effect that the connection
        # will be closed.
        #
        raise RuntimeError("Unexpected CHOKE message")

    def got_unchoke(self, stream):
        if self.state != SENT_INTERESTED:
            raise RuntimeError("UNCHOKE when state != SENT_INTERESTED")
        else:
            self.state = DOWNLOADING

            #
            # We just need to send one request to tell
            # the peer we would like the download to start.
            #
            if self.version >= 2:
                logging.info('BitTorrent: download in progress...')
                index = random.randrange(self.numpieces)
                stream.send_request(index, 0, PIECE_LEN)
                return

            #
            # When we're unchoked immediately pipeline a number
            # of requests and then put another request on the pipe
            # as soon as a piece arrives.  Note that the pipelining
            # is automagically done by the scheduler generator.
            # The idea of pipelining is that of filling with many
            # messages the space between us and the peer to do
            # something that approxymates a continuous download.
            #
            logging.info("BitTorrent: downloading %d bytes in progress...",
              self.target_bytes)
            burst = self.sched_req.next()
            for index, begin, length in burst:
                stream.send_request(index, begin, length)
                self.inflight += 1

    def got_have(self, index):
        if self.state != UPLOADING:
            raise RuntimeError("HAVE when state != UPLOADING")
        self.peer_bitfield[index] = 1
        # We don't use HAVE messages at the moment
        logging.warning("Ignoring unexpected HAVE message")

    def got_piece(self, *args):

        stream = args[0]

        if self.state != DOWNLOADING:
            raise RuntimeError("PIECE when state != DOWNLOADING")

        # Start measuring
        if not self.saved_ticks:
            self.saved_bytes = stream.bytes_recv_tot
            self.saved_ticks = utils.ticks()

        #
        # The download is driven by the sender and
        # we just need to discard the pieces.
        # Periodically send some requests to the other
        # end, with probability 10%.
        #
        if self.version >= 2:
            if self.version == 3 or random.random() < 0.1:
                index = random.randrange(self.numpieces)
                stream.send_request(index, 0, PIECE_LEN)
            return

        self.get_piece_old(stream)

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
    def get_piece_old(self, stream):
        ''' implements get_piece() for test version 1 '''

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

                logging.info("BitTorrent: downloading %d bytes ... %s",
                  self.target_bytes, utils.speed_formatter(speed))

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
                        STATE.update("test_progress", "50%", publish=False)
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

def main(args):
    ''' Main function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'lO:v')
    except getopt.error:
        sys.exit('usage: neubot bittorrent_peer [-lv] [-O setting]')
    if arguments:
        sys.exit('usage: neubot bittorrent_peer [-lv] [-O setting]')

    settings = [ 'address "127.0.0.1 ::1"',
                 'port 6881',
                 'version 1' ]

    listener = False
    for name, value in options:
        if name == '-l':
            listener = True
        elif name == '-O':
            settings.append(value)
        elif name == '-v':
            CONFIG['verbose'] = 1

    settings = utils_rc.parse_safe(iterable=settings)

    config_copy = CONFIG.copy()
    config.finalize_conf(config_copy)

    peer = PeerNeubot(POLLER)
    peer.configure(config_copy)  # BLEAH
    peer.version = int(settings['version'])
    if not listener:
        peer.connect((settings['address'], int(settings['port'])))
    else:
        peer.listen((settings['address'], int(settings['port'])))

    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
