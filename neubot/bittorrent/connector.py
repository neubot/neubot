# neubot/bittorrent/connector.py

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

from cStringIO import StringIO
from handler import Handler
from bitfield import Bitfield

def toint(s):
    return struct.unpack("!i", s)[0]

def tobinary(i):
    return struct.pack("!i", i)

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







class BTConnector(Handler):
    """Implements the syntax of the BitTorrent protocol.
       See Upload.py and Download.py for the connection-level
       semantics."""

    def __init__(self, parent, connection, id, is_local,
                 obfuscate_outgoing=False, log_prefix = "", lan=False):
        self.parent = parent
        self.connection = connection
        self.id = id
        self.ip = connection.ip
        self.port = connection.port
        self.addr = (self.ip, self.port)
        self.hostname = None
        self.locally_initiated = is_local
        if self.locally_initiated:
            self.max_message_length = self.parent.config['max_message_length']
            self.listening_port = self.port
        else:
            self.listening_port = None
        self.complete = False
        self.lan = lan
        self.closed = False
        self.got_anything = False
        self.upload = None
        self.download = None
        self._buffer = StringIO()
        self._reader = self._read_messages()
        self._next_len = self._reader.next()
        self._message = None


        self.obfuscate_outgoing = obfuscate_outgoing
        self.sloppy_pre_connection_counter = 0
        self.log_prefix = log_prefix


        #XXX different with original code: attach BEFORE handshake
        self.connection.attach_connector(self)
        if self.locally_initiated:
            self.send_handshake()


    def send_handshake(self):

            self.connection.write(''.join((chr(len(protocol_name)),
                                           protocol_name,
                                           FLAGS,
                                           self.parent.infohash)))
            # if we already have the peer's id, just send ours.
            # otherwise we wait for it.
            if self.id is not None:
                self.connection.write(self.parent.my_id)


    def close(self):
        if not self.closed:
            self.connection.close()

    def send_interested(self):
        self._send_message(INTERESTED)

    def send_not_interested(self):
        self._send_message(NOT_INTERESTED)

    def send_choke(self):
            self._send_message(CHOKE)

    def send_unchoke(self):
            self._send_message(UNCHOKE)


    def send_request(self, index, begin, length):
        self._send_message(struct.pack("!ciii", REQUEST, index, begin, length))

    def send_cancel(self, index, begin, length):
        self._send_message(struct.pack("!ciii", CANCEL, index, begin, length))

    def send_bitfield(self, bitfield):
        self._send_message(BITFIELD, bitfield)

    def send_have(self, index):
        self._send_message(struct.pack("!ci", HAVE, index))





    def send_keepalive(self):
        self._send_message('')







    # yields the number of bytes it wants next, gets those in self._message
    def _read_messages(self):

        # be compatible with encrypted clients. Thanks Uoti
        yield 1 + len(protocol_name)


        yield 20 # download id (i.e., infohash)

        if not self.locally_initiated:
            self.connection.write(''.join((chr(len(protocol_name)),
                                           protocol_name, FLAGS,
                                           self.parent.infohash,
                                           self.parent.my_id)))

        yield 20  # peer id
        # if we don't already have the peer's id, send ours
        if not self.id:
            self.id = self._message



            if self.locally_initiated:
                self.connection.write(self.parent.my_id)


        self.complete = True
        self.parent.connection_handshake_completed(self)

        while True:
            yield 4   # message length
            l = toint(self._message)
            if l > self.max_message_length:
                return
            if l > 0:
                yield l
                self._got_message(self._message)




    def _got_message(self, message):
        t = message[0]
        #XXX we have removed HAVE_ALL and HAVE_NONE
        #if t in [BITFIELD, HAVE_ALL, HAVE_NONE] and self.got_anything:
        if t in [BITFIELD] and self.got_anything:
            self.close()
            return
        self.got_anything = True
        #XXX We have removed HAVE_ALL and HAVE_NONE
        if (t in (CHOKE, UNCHOKE, INTERESTED, NOT_INTERESTED,
                  ) and
                len(message) != 1):
            self.close()
            return
        if t == CHOKE:
            pass
        elif t == UNCHOKE:
            pass
        elif t == INTERESTED:
            pass
        elif t == NOT_INTERESTED:
            pass
        elif t == HAVE:
            pass
        elif t == BITFIELD:
            pass
        elif t == REQUEST:
            if len(message) != 13:
                self.close()
                return
            i, a, b = struct.unpack("!xiii", message)
            self.upload.got_request(i, a, b)
        elif t == CANCEL:
            pass
        elif t == PIECE:
            if len(message) <= 9:
                self.close()
                return
            n = len(message) - 9
            i, a, b = struct.unpack("!xii%ss" % n, message)
            self.download.got_piece(i, a, b)
        else:
            self.close()

    def _write(self, s):
            self.connection.write(s)

    def _send_message(self, *msg_a):
        if self.closed:
            return
        l = 0
        for e in msg_a:
            l += len(e)
        d = [tobinary(l), ]
        d.extend(msg_a)
        s = ''.join(d)
        self._write(s)

    def data_came_in(self, conn, s):
        while True:
            if self.closed:
                return
            i = self._next_len - self._buffer.tell()
            if i > len(s):
                # not enough bytes, keep buffering
                self._buffer.write(s)
                return
            if self._buffer.tell() > 0:
                # collect buffer + current for message
                self._buffer.write(buffer(s, 0, i))
                m = self._buffer.getvalue()
                # optimize for cpu (reduce mallocs)
                #self._buffer.truncate(0)
                # optimize for memory (free buffer memory)
                self._buffer.close()
                self._buffer = StringIO()
            else:
                # painful string copy
                m = s[:i]
            s = buffer(s, i)
            self._message = m
            self._rest = s
            try:
                self._next_len = self._reader.next()
            except StopIteration:
                self.close()
                return
            except:
                self.close()
                return


    def connection_lost(self, conn):
        self.closed = True
        self._reader = None
        self.parent.connection_lost(self)


        self.connection = None
        if self.complete:
            self.upload = None
            self.download = None
        del self._buffer
        del self.parent
        del self._message

    def connection_flushed(self, connection):
        pass
