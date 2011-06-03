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

from neubot.bittorrent.bitfield import Bitfield
from neubot.bittorrent.stream import StreamBitTorrent
from neubot.net.stream import StreamHandler

from neubot import utils

NUMPIECES = 1<<20

def random_bytes(n):
    return "".join([chr(random.randint(32, 126)) for _ in range(n)])

class Peer(StreamHandler):
    def __init__(self, poller):
        StreamHandler.__init__(self, poller)
        self.numpieces = NUMPIECES
        self.bitfield = Bitfield(NUMPIECES)
        self.peer_bitfield = Bitfield(NUMPIECES)
        self.infohash = random_bytes(20)
        self.my_id = random_bytes(20)
        self.interested = False
        self.choked = True

    def connection_ready(self, stream):
        """Invoked when the handshake is complete."""

    def connection_made(self, sock):
        stream = StreamBitTorrent(self.poller)
        stream.attach(self, sock, self.conf, self.measurer)

    def got_bitfield(self, b):
        self.peer_bitfield = b

    # Upload

    def got_request(self, stream, index, begin, length):
        """Invoked when you receive a request."""

    def got_interested(self, stream):
        self.interested = True
        stream.send_unchoke()

    def got_not_interested(self, stream):
        self.interested = False
        stream.send_choke()

    # Download

    def got_choke(self, stream):
        self.choked = True

    def got_unchoke(self, stream):
        self.choked = False

    def got_have(self, index):
        self.peer_bitfield[index] = 1

    def got_piece(self, stream, index, begin, block):
        self.piece_start(stream, index, begin, "")
        self.piece_part(stream, index, begin, block)
        self.piece_end(stream, index, begin)

    def piece_start(self, stream, index, begin, block):
        """Invoked when a piece starts."""

    def piece_part(self, stream, index, begin, block):
        """Invoked when you receive a portion of a piece."""

    def piece_end(self, stream, index, begin):
        """Invoked at the end of the piece."""
