# neubot/bittorrent/server.py

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

from neubot.negotiate.server_bittorrent import NEGOTIATE_SERVER_BITTORRENT
from neubot.bittorrent.peer import PeerNeubot
from neubot.bittorrent.config import _random_bytes

from neubot import utils

#
# The BitTorrent server must not change its PEER_ID
# each time a new client connects.  Instead it should
# keep using the same identifier over and over and
# over.
#
MY_ID = _random_bytes(20)

#
# We check whether a peer is authorized or not just at
# the beginning and from then on we rely on the watchdog
# mechanism that guarantees that at a point the stream
# will be closed anyway.
# We save just our download_speed which is indeed the
# peer's upload speed, the timestamp and the target bytes
# for the next test.
#
class ServerPeer(PeerNeubot):

    def configure(self, conf):
        conf["bittorrent.my_id"] = MY_ID
        PeerNeubot.configure(self, conf)

    def connection_ready(self, stream):
        if not stream.id in NEGOTIATE_SERVER_BITTORRENT.peers:
            raise RuntimeError("Unauthorized peer")

        #
        # Override the number of bytes using information passed
        # from the peer and regenerate the schedule so that we
        # actually transfer that number of bytes.
        # Override the test_version information as well.
        #
        self.target_bytes = NEGOTIATE_SERVER_BITTORRENT.peers[stream.id][
                                                   "target_bytes"]
        self.version = NEGOTIATE_SERVER_BITTORRENT.peers[stream.id][
                                                   "test_version"]
        self.make_sched()

        PeerNeubot.connection_ready(self, stream)

    def complete(self, stream, speed, rtt, target_bytes):
        # Avoid leak: do not add an entry if not needed
        if stream.id in NEGOTIATE_SERVER_BITTORRENT.peers:
            NEGOTIATE_SERVER_BITTORRENT.peers[stream.id] = {
                                     "upload_speed": speed,
                                     "timestamp": utils.timestamp(),
                                     "target_bytes": target_bytes,
                                    }
