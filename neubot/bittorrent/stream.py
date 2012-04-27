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
# Modified for Neubot by Simone Basso <bassosimone@gmail.com>
#

''' BitTorrent peer wire protocol implementation '''

import struct
import logging

from neubot.bittorrent.config import MAXMESSAGE

from neubot.net.stream import Stream

# Available msgs
MESSAGES = (CHOKE, UNCHOKE, INTERESTED, NOT_INTERESTED, HAVE, BITFIELD,
            REQUEST, PIECE, CANCEL) = [chr(num) for num in range(9)]

# Set of available msgs
MESSAGESET = set(MESSAGES)

# Each message type has it's length checker
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

# Flags used during handshake
FLAGS = ['\0'] * 8
FLAGS = ''.join(FLAGS)

# Protocol name (for handshake)
PROTOCOL_NAME = 'BitTorrent protocol'

def toint(data):
    ''' Converts binary data to integer '''
    return struct.unpack("!I", data)[0]

def tobinary(integer):
    ''' Converts integer to binary data '''
    return struct.pack("!I", integer)

class StreamBitTorrent(Stream):

    ''' BitTorrent stream '''

    def __init__(self, poller):
        ''' Initialize BitTorrent stream '''
        Stream.__init__(self, poller)
        self.complete = False
        self.got_anything = False
        # This is the size of the handshake
        self.left = 68
        self.buff = []
        self.count = 0
        self.id = None
        self.piece = None

    def connection_made(self):
        ''' Invoked when the connection is established '''
        #
        # In Neubot the listener does not have an infohash
        # and handshakes, including connector infohash, after
        # it receives the connector handshake.
        #
        if self.parent.infohash:
            self._send_handshake()
        self.start_recv()

    def _send_handshake(self):
        ''' Convenience function to send handshake '''
        logging.debug("> HANDSHAKE infohash=%s id=%s",
                      self.parent.infohash.encode("hex"),
                      self.parent.my_id.encode("hex"))
        self.start_send("".join((chr(len(PROTOCOL_NAME)), PROTOCOL_NAME,
          FLAGS, self.parent.infohash, self.parent.my_id)))

    def send_interested(self):
        ''' Send the INTERESTED message '''
        logging.debug("> INTERESTED")
        self._send_message(INTERESTED)

    def send_not_interested(self):
        ''' Send the NOT_INTERESTED message '''
        logging.debug("> NOT_INTERESTED")
        self._send_message(NOT_INTERESTED)

    def send_choke(self):
        ''' Send the CHOKE message '''
        logging.debug("> CHOKE")
        self._send_message(CHOKE)

    def send_unchoke(self):
        ''' Send the UNCHOKE message '''
        logging.debug("> UNCHOKE")
        self._send_message(UNCHOKE)

    def send_request(self, index, begin, length):
        ''' Send the REQUEST message '''
        logging.debug("> REQUEST %d %d %d", index, begin, length)
        self._send_message(struct.pack("!cIII", REQUEST, index, begin, length))

    def send_cancel(self, index, begin, length):
        ''' Send the CANCEL message '''
        logging.debug("> CANCEL %d %d %d", index, begin, length)
        self._send_message(struct.pack("!cIII", CANCEL, index, begin, length))

    def send_bitfield(self, bitfield):
        ''' Send the BITFIELD message '''
        logging.debug("> BITFIELD {bitfield}")
        self._send_message(BITFIELD, bitfield)

    def send_have(self, index):
        ''' Send the HAVE message '''
        logging.debug("> HAVE %d", index)
        self._send_message(struct.pack("!cI", HAVE, index))

    def send_keepalive(self):
        ''' Send the KEEPALIVE message '''
        logging.debug("> KEEPALIVE")
        self._send_message('')

    def send_piece(self, index, begin, block):
        ''' Send the PIECE message '''
        logging.debug("> PIECE %d %d len=%d", index, begin, len(block))
        self._send_message(struct.pack("!cII%ss" % len(block), PIECE,
          index, begin, block))

    def _send_message(self, *msg_a):
        ''' Convenience function to send a message '''
        l = 0
        for e in msg_a:
            l += len(e)
        d = [tobinary(l), ]
        d.extend(msg_a)
        s = ''.join(d)
        self.start_send(s)

    def send_complete(self):
        ''' Invoked when the send queue is empty '''
        self.parent.send_complete(self)

    #
    # We use three state variables in this loop: self.left is the
    # size left to read in the next message, self.count is the amount
    # of bytes we've read so far, and self.buff contains a portion
    # of the next message.
    #
    def recv_complete(self, s):

        ''' Invoked when recv() completes '''

        while s and not (self.close_pending or self.close_complete):

            # If we don't know the length then read it
            if self.left == 0:
                amt = min(len(s), 4 - self.count)
                self.buff.append(s[:amt])
                s = buffer(s, amt)
                self.count += amt

                if self.count == 4:
                    self.left = toint("".join(self.buff))
                    if self.left == 0:
                        logging.debug("< KEEPALIVE")
                    elif self.left > MAXMESSAGE:
                        raise RuntimeError('Message too big')
                    del self.buff[:]
                    self.count = 0

                elif self.count > 4:
                    raise RuntimeError("Invalid self.count")

            # Bufferize and pass upstream messages
            elif self.left > 0:
                amt = min(len(s), self.left)
                self.buff.append(s[:amt])
                s = buffer(s, amt)
                self.left -= amt
                self.count += amt

                if self.left == 0:
                    self._got_message("".join(self.buff))
                    del self.buff[:]
                    self.count = 0

                elif self.left < 0:
                    raise RuntimeError("Invalid self.left")

            # Something's wrong
            else:
                raise RuntimeError("Invalid self.left")

        if not (self.close_pending or self.close_complete):
            self.start_recv()

    def _got_message(self, message):

        ''' Invoked when we receive a complete message '''

        if not self.complete:
            if (len(message) != 68 or message[0] != chr(19) or
               message[1:20] != PROTOCOL_NAME):
                raise RuntimeError("Invalid handshake")
            self.id = message[-20:]
            infohash = message[-40:-20]
            logging.debug("< HANDSHAKE infohash=%s id=%s",
                          infohash.encode("hex"), self.id.encode("hex"))

            #
            # In Neubot the listener does not have an infohash
            # and handshakes, including connector infohash, after
            # it receives the connector handshake.
            #
            if not self.parent.infohash:
                self.parent.infohash = infohash
                self._send_handshake()
            elif infohash != self.parent.infohash:
                raise RuntimeError("Invalid infohash")

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
            logging.debug("< CHOKE")
            self.parent.got_choke(self)

        elif t == UNCHOKE:
            logging.debug("< UNCHOKE")
            self.parent.got_unchoke(self)

        elif t == INTERESTED:
            logging.debug("< INTERESTED")
            self.parent.got_interested(self)

        elif t == NOT_INTERESTED:
            logging.debug("< NOT_INTERESTED")
            self.parent.got_not_interested(self)

        elif t == HAVE:
            i = struct.unpack("!xI", message)[0]
            if i >= self.parent.numpieces:
                raise RuntimeError("HAVE: index out of bounds")
            logging.debug("< HAVE %d", i)
            self.parent.got_have(i)

        elif t == BITFIELD:
            logging.debug("< BITFIELD {bitfield}")
            self.parent.got_bitfield(message[1:])

        elif t == REQUEST:
            i, a, b = struct.unpack("!xIII", message)
            logging.debug("< REQUEST %d %d %d", i, a, b)
            if i >= self.parent.numpieces:
                raise RuntimeError("REQUEST: index out of bounds")
            self.parent.got_request(self, i, a, b)

        elif t == CANCEL:
            i, a, b = struct.unpack("!xIII", message)
            logging.debug("< CANCEL %d %d %d", i, a, b)
            if i >= self.parent.numpieces:
                raise RuntimeError("CANCEL: index out of bounds")
            # NOTE Ignore CANCEL message

        elif t == PIECE:
            n = len(message) - 9
            i, a, b = struct.unpack("!xII%ss" % n, message)
            logging.debug("< PIECE %d %d len=%d", i, a, n)
            if i >= self.parent.numpieces:
                raise RuntimeError("PIECE: index out of bounds")
            self.parent.got_piece(self, i, a, b)

    def connection_lost(self, exception):
        ''' Invoked when the connection is lost '''
        del self.buff[:]
