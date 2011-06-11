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

from neubot.net.stream import Stream
from neubot.log import LOG

from neubot import utils

MESSAGES = [CHOKE, UNCHOKE, INTERESTED, NOT_INTERESTED, HAVE, BITFIELD,
            REQUEST, PIECE, CANCEL] = map(chr, range(9))

MESSAGESET = set(MESSAGES)

INVALID_LENGTH = {
    CHOKE: lambda l: l != 1,
    UNCHOKE: lambda l: l != 1,
    INTERESTED: lambda l: l != 1,
    NOT_INTERESTED: lambda l: l != 1,
    HAVE: lambda l: l != 5,
    BITFIELD: lambda l: l <= 1,
    REQUEST: lambda l: l != 13,
    PIECE: lambda l: l <= 9,
    CANCEL: lambda l: l != 13,
}

FLAGS = ['\0'] * 8
FLAGS = ''.join(FLAGS)
PROTOCOL_NAME = 'BitTorrent protocol'

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
    return struct.unpack("!I", s)[0]

def tobinary(i):
    return struct.pack("!I", i)

#
# Keep safe the parameters of PIECE messages
# for very large piece messages, that are not
# buffered and passed as a single bag of bytes
# to the message-reading code.
#
class PieceMessage(object):
    def __init__(self, index, begin):
        self.index = index
        self.begin = begin

#
# Specializes stream in order to handle the BitTorrent peer
# wire protocol.  See also the finite state machine documented
# at `doc/protocol.png`.
# Note that we start with left = 68 because that is the size
# of the BitTorrent handshake.
#
class StreamBitTorrent(Stream):
    def __init__(self, poller):
        Stream.__init__(self, poller)
        self.complete = False
        self.closing = False
        self.writing = False
        self.got_anything = False
        self.left = 68
        self.buff = []
        self.count = 0
        self.id = None
        self.piece = None

    def connection_made(self):
        LOG.debug("> HANDSHAKE")
        self.start_send("".join((chr(len(PROTOCOL_NAME)), PROTOCOL_NAME,
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
        self._send_message(struct.pack("!cIII", REQUEST, index, begin, length))

    def send_cancel(self, index, begin, length):
        LOG.debug("> CANCEL %d %d %d" % (index, begin, length))
        self._send_message(struct.pack("!cIII", CANCEL, index, begin, length))

    def send_bitfield(self, bitfield):
        LOG.debug("> BITFIELD {bitfield}")
        self._send_message(BITFIELD, bitfield)

    def send_have(self, index):
        LOG.debug("> HAVE %d" % index)
        self._send_message(struct.pack("!cI", HAVE, index))

    def send_keepalive(self):
        LOG.debug("> KEEPALIVE")
        self._send_message('')

    def send_piece(self, index, begin, block):
        if not isinstance(block, basestring):
            length = utils.file_length(block)
            LOG.debug("> PIECE %d %d len=%d" % (index, begin, length))
            preamble = struct.pack("!cII", PIECE, index, begin)
            l = len(preamble) + length
            d = [tobinary(l), ]
            d.extend(preamble)
            s = "".join(d)
            self.start_send(s)
            self.start_send(block)
            return

        LOG.debug("> PIECE %d %d len=%d" % (index, begin, len(block)))
        self._send_message(struct.pack("!cII%ss" % len(block), PIECE,
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
                    if self.left == 0:
                        LOG.debug("< KEEPALIVE")
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
        i, a, b = struct.unpack("!xII%ss" % n, message)
        if self.piece:
            raise RuntimeError("Jumbo message not ended properly")
        self.piece = PieceMessage(i, a)
        self.parent.piece_start(self, i, a, b)

    def _got_message_part(self, s):
        self.parent.piece_part(self, self.piece.index, self.piece.begin, s)

    def _got_message_end(self):
        self.parent.piece_end(self, self.piece.index, self.piece.begin)
        self.piece = None

    def _got_message(self, message):

        if not self.complete:
            if (len(message) != 68 or message[0] != chr(19) or
               message[1:20] != PROTOCOL_NAME):
                raise RuntimeError("Invalid handshake")
            LOG.debug("< HANDSHAKE")
            if not self.id:
                self.id = message[-20:]
            self.complete = True
            self.parent.connection_ready(self)
            return

        t = message[0]
        if t not in MESSAGESET:
            raise RuntimeError("Invalid message type")
        if INVALID_LENGTH[t](len(message)):
            raise RuntimeError("Invalid message length")
        if t in [BITFIELD] and self.got_anything:
            raise RuntimeError("Bitfield after we got something")
        self.got_anything = True

        if t == CHOKE:
            LOG.debug("< CHOKE")
            self.parent.got_choke(self)

        elif t == UNCHOKE:
            LOG.debug("< UNCHOKE")
            self.parent.got_unchoke(self)

        elif t == INTERESTED:
            LOG.debug("< INTERESTED")
            self.parent.got_interested(self)

        elif t == NOT_INTERESTED:
            LOG.debug("< NOT_INTERESTED")
            self.parent.got_not_interested(self)

        elif t == HAVE:
            i = struct.unpack("!xI", message)[0]
            if i >= self.parent.numpieces:
                raise RuntimeError("HAVE: index out of bounds")
            LOG.debug("< HAVE %d" % i)
            self.parent.got_have(i)

        elif t == BITFIELD:
            LOG.debug("< BITFIELD {bitfield}")
            self.parent.got_bitfield(message[1:])

        elif t == REQUEST:
            i, a, b = struct.unpack("!xIII", message)
            LOG.debug("< REQUEST %d %d %d" % (i, a, b))
            if i >= self.parent.numpieces:
                raise RuntimeError("REQUEST: index out of bounds")
            self.parent.got_request(self, i, a, b)

        elif t == CANCEL:
            i, a, b = struct.unpack("!xIII", message)
            LOG.debug("< CANCEL %d %d %d" % (i, a, b))
            if i >= self.parent.numpieces:
                raise RuntimeError("CANCEL: index out of bounds")
            # NOTE Ignore CANCEL message

        elif t == PIECE:
            n = len(message) - 9
            i, a, b = struct.unpack("!xII%ss" % n, message)
            LOG.debug("< PIECE %d %d len=%d" % (i, a, n))
            if i >= self.parent.numpieces:
                raise RuntimeError("PIECE: index out of bounds")
            self.parent.got_piece(self, i, a, b)

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
        del self.buff[:]
