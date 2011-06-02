# neubot/bittorrent/stream.py

#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Originally written by Bram Cohen, heavily modified by Uoti Urpala
# Fast extensions added by David Harrison
# Modified for neubot by Simone Basso <bassosimone@gmail.com>
#

import struct
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.bittorrent.bitfield import Bitfield
from neubot.net.stream import Stream
from neubot.log import LOG

from neubot import utils

CHOKE = chr(0)
UNCHOKE = chr(1)
INTERESTED = chr(2)
NOT_INTERESTED = chr(3)
HAVE = chr(4)
BITFIELD = chr(5)
REQUEST = chr(6)
PIECE = chr(7)
CANCEL = chr(8)

FLAGS = ['\0'] * 8
FLAGS = ''.join(FLAGS)
protocol_name = 'BitTorrent protocol'

#
# When messages are bigger than SMALLMESSAGE we stop
# buffering the whole message and we pass upstream the
# incoming chunks.
# Note that SMALLMESSAGE is the maximum message size
# suggested by BEP 0003 ("All current implementations
# close connections which request an amount greater
# than 2^17").
# So, the original behavior is preserved for messages
# in the expected range, and we avoid buffering for
# jumbo messages only.
#
SMALLMESSAGE = 1<<17

def toint(s):
    return struct.unpack("!i", s)[0]

def tobinary(i):
    return struct.pack("!i", i)

class BTStream(Stream):

    """Specializes stream in order to handle the BitTorrent peer
       wire protocol.  See also the finite state machine documented
       at `doc/protocol.png`."""

    def initialize(self, parent, id, locally_initiated):
        self.parent = parent
        self.id = id
        self.hostname = None
        self.locally_initiated = locally_initiated
        self.complete = False
        self.closing = False
        self.writing = False
        self.got_anything = False
        self.upload = None
        self.download = None
        self.left = 68
        self.buff = []
        self.count = 0

    def connection_made(self):
        LOG.debug("> HANDSHAKE")
        self.start_send("".join((chr(len(protocol_name)), protocol_name,
          FLAGS, self.parent.infohash, self.parent.my_id)))
        self.start_recv()

    def send_interested(self):
        LOG.debug("> INTERESTED")
        self._send_message(INTERESTED)

    def send_not_interested(self):
        LOG.debug("> NOT_INTERESTED")
        self._send_message(NOT_INTERESTED)

    def send_choke(self):
        LOG.debug("> CHOKE")
        self._send_message(CHOKE)

    def send_unchoke(self):
        LOG.debug("> UNCHOKE")
        self._send_message(UNCHOKE)

    def send_request(self, index, begin, length):
        LOG.debug("> REQUEST %d %d %d" % (index, begin, length))
        self._send_message(struct.pack("!ciii", REQUEST, index, begin, length))

    def send_cancel(self, index, begin, length):
        LOG.debug("> CANCEL %d %d %d" % (index, begin, length))
        self._send_message(struct.pack("!ciii", CANCEL, index, begin, length))

    def send_bitfield(self, bitfield):
        LOG.debug("> BITFIELD <bitfield>")
        self._send_message(BITFIELD, bitfield)

    def send_have(self, index):
        LOG.debug("> HAVE %d" % index)
        self._send_message(struct.pack("!ci", HAVE, index))

    def send_keepalive(self):
        LOG.debug("> KEEPALIVE")
        self._send_message('')

    def send_piece(self, index, begin, block):
        if not isinstance(block, basestring):
            length = utils.file_length(block)
            LOG.debug("> PIECE %d %d len=%d" % (index, begin, length))
            preamble = struct.pack("!cii", PIECE, index, begin)
            l = len(preamble) + length
            d = [tobinary(l), ]
            d.extend(preamble)
            s = "".join(d)
            self.start_send(s)
            self.start_send(block)
            return

        LOG.debug("> PIECE %d %d len=%d" % (index, begin, len(block)))
        self._send_message(struct.pack("!cii%ss" % len(block), PIECE,
          index, begin, block))

    def _send_message(self, *msg_a):
        if self.closing:
            return
        self.writing = True
        l = 0
        for e in msg_a:
            l += len(e)
        d = [tobinary(l), ]
        d.extend(msg_a)
        s = ''.join(d)
        self.start_send(s)

    def send_complete(self):
        self.writing = False
        if self.closing:
            self.shutdown()

    #
    # We use three state variables in this loop: self.left is the
    # size left to read in the next message, self.count is the amount
    # of bytes we've read so far, and self.buff contains a portion
    # of the next message.
    #
    def recv_complete(self, s):
        while s and not self.closing:

            # If we don't know the length then read it
            if self.left == 0:
                amt = min(len(s), 4)
                self.buff.append(s[:amt])
                s = buffer(s, amt)
                self.count += amt

                if self.count == 4:
                    self.left = toint("".join(self.buff))
                    if self.left < 0:
                        raise RuntimeError("Message length overflow")
                    del self.buff[:]
                    self.count = 0

            # Bufferize and pass upstream messages
            else:
                amt = min(len(s), self.left)
                if self.count <= SMALLMESSAGE:
                    self.buff.append(s[:amt])
                else:
                    if self.buff:
                        self._got_message_start("".join(self.buff))
                        del self.buff[:]
                    mp = buffer(s, 0, amt)
                    self._got_message_part(mp)
                s = buffer(s, amt)
                self.left -= amt
                self.count += amt

                if self.left == 0:
                    if self.buff:
                        self._got_message("".join(self.buff))
                    else:
                        self._got_message_end()
                    del self.buff[:]
                    self.count = 0

        if not self.closing:
            self.start_recv()

    def _got_message_start(self, message):
        t = message[0]
        if t != PIECE:
            raise RuntimeError("unexpected jumbo message")
        if len(message) <= 9:
            raise RuntimeError("PIECE: invalid message length")
        n = len(message) - 9
        i, a, b = struct.unpack("!xii%ss" % n, message)
        self.download.piece_start(i, a, b)

    def _got_message_part(self, s):
        self.download.piece_part(s)

    def _got_message_end(self):
        self.download.piece_end()

    def _got_message(self, message):
        if not self.complete:
            LOG.debug("< HANDSHAKE")
            if not self.id:
                self.id = message[-20:]
            self.complete = True
            self.parent.connection_handshake_completed(self)
            return
        t = message[0]
        if t in [BITFIELD] and self.got_anything:
            raise RuntimeError("Bitfield after we got something")
        self.got_anything = True
        if (t in (CHOKE, UNCHOKE, INTERESTED, NOT_INTERESTED) and
          len(message) != 1):
            raise RuntimeError("Expecting one-byte-long message, got more")
        if t == CHOKE:
            LOG.debug("< CHOKE")
            self.download.got_choke()
        elif t == UNCHOKE:
            LOG.debug("< UNCHOKE")
            self.download.got_unchoke()
        elif t == INTERESTED:
            LOG.debug("< INTERESTED")
            self.upload.got_interested()
        elif t == NOT_INTERESTED:
            LOG.debug("< NOT_INTERESTED")
            self.upload.got_not_interested()
        elif t == HAVE:
            pass
        elif t == BITFIELD:
            pass
        elif t == REQUEST:
            if len(message) != 13:
                raise RuntimeError("REQUEST: invalid message length")
            i, a, b = struct.unpack("!xiii", message)
            LOG.debug("< REQUEST %d %d %d" % (i, a, b))
            self.upload.got_request(i, a, b)
        elif t == CANCEL:
            pass
        elif t == PIECE:
            if len(message) <= 9:
                raise RuntimeError("PIECE: invalid message length")
            n = len(message) - 9
            i, a, b = struct.unpack("!xii%ss" % n, message)
            LOG.debug("< PIECE %d %d len=%d" % (i, a, n))
            self.download.got_piece(i, a, b)
        else:
            raise RuntimeError("Unexpected message type")

    def close(self):
        if self.closing:
            return
        LOG.debug("* Requested to close connection %s" % self.logname)
        self.closing = True
        if self.writing:
            return
        self.shutdown()

    def connection_lost(self, exception):
        # because we might also be invoked on network error
        self.closing = True
        self.upload = None
        self.download = None
        self.parent = None
        del self.buff[:]
