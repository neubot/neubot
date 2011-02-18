# neubot/bittorrent/streams.py

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

import cStringIO
import struct
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.bittorrent.bitfield import Bitfield
from neubot.net.streams import Stream

from neubot.net.streams import verboser as VERBOSER
from neubot.log import log as LOG

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

MAX_MESSAGE_LENGTH = 1<<16

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
        self._buffer = cStringIO.StringIO()
        self._reader = self._read_messages()
        self._next_len = self._reader.next()
        self._message = None

    def connection_made(self):
        VERBOSER.connection_made(self.logname)
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

    def recv_complete(self, s):
        while True:
            if self.closing:
                return
            i = self._next_len - self._buffer.tell()
            if i > len(s):
                self._buffer.write(s)
                break
            if self._buffer.tell() > 0:
                self._buffer.write(buffer(s, 0, i))
                m = self._buffer.getvalue()
                self._buffer.close()
                self._buffer = cStringIO.StringIO()
            else:
                m = s[:i]
            s = buffer(s, i)
            self._message = m
            self._rest = s
            try:
                self._next_len = self._reader.next()
            except StopIteration:
                self.close()
                return
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                self.close()
                return
        self.start_recv()

    def _read_messages(self):
        yield 1 + len(protocol_name) + 8 + 20 + 20
        LOG.debug("< HANDSHAKE")
        if not self.id:
            self.id = self._message
        self.complete = True
        self.parent.connection_handshake_completed(self)
        while True:
            yield 4
            l = toint(self._message)
            LOG.debug("BT receiver: expect %d bytes" % l)
            if l > MAX_MESSAGE_LENGTH:
                return
            if l > 0:
                yield l
                LOG.debug("BT receiver: got %d bytes" % l)
                self._got_message(self._message)

    def _got_message(self, message):
        t = message[0]
        if t in [BITFIELD] and self.got_anything:
            self.close()
            return
        self.got_anything = True
        if (t in (CHOKE, UNCHOKE, INTERESTED, NOT_INTERESTED) and
          len(message) != 1):
            self.close()
            return
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
                self.close()
                return
            i, a, b = struct.unpack("!xiii", message)
            LOG.debug("< REQUEST %d %d %d" % (i, a, b))
            self.upload.got_request(i, a, b)
        elif t == CANCEL:
            pass
        elif t == PIECE:
            if len(message) <= 9:
                self.close()
                return
            n = len(message) - 9
            i, a, b = struct.unpack("!xii%ss" % n, message)
            LOG.debug("< PIECE %d %d len=%d" % (i, a, n))
            self.download.got_piece(i, a, b)
        else:
            self.close()

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
        VERBOSER.connection_lost(self.logname, self.eof, exception)
        self._reader = None
        self.parent.connection_lost(self)
        self.upload = None
        self.download = None
        self._buffer = None
        self.parent = None
        self._message = None
