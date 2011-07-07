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

import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.bittorrent.negotiate import AUTH_PEERS
from neubot.bittorrent.peer import PeerNeubot
from neubot.config import CONFIG
from neubot.http.server import HTTP_SERVER
from neubot.log import LOG
from neubot.net.poller import POLLER

from neubot import boot
from neubot import system
from neubot import utils

#
# We check whether a peer is authorized or not just at
# the beginning and from then on we rely on the watchdog
# mechanism that guarantees that at a point the stream
# will be closed anyway.
# We save just our download_speed which is indeed the
# peer's upload speed and the timestamp.
#
class ServerPeer(PeerNeubot):
    def connection_ready(self, stream):
        if not stream.id in AUTH_PEERS:
            raise RuntimeError("Unauthorized peer")
        # Not needed: peer.py already does that
        #stream.watchdog = 30
        PeerNeubot.connection_ready(self, stream)

    def complete(self, stream, speed, rtt):
        # Avoid leak: do not add an entry if not needed
        if stream.id in AUTH_PEERS:
            AUTH_PEERS[stream.id] = {
                                     "upload_speed": speed,
                                     "timestamp": utils.timestamp(),
                                    }

#XXX These should all go into the same file
CONFIG.register_defaults({
    "bittorrent.address": "0.0.0.0",
    "bittorrent.daemonize": True,
    "bittorrent.http_port": 80,
    "bittorrent.bt_port": 6881,
})

def main(args):
    CONFIG.register_descriptions({
        "bittorrent.address": "Address to listen to",
        "bittorrent.daemonize": "Become a daemon",
        "bittorrent.http_port": "HTTP port to listen to",
        "bittorrent.bt_port": "BitTorrent port to listen to",
    })

    boot.common("bittorrent.server", "BitTorrent test server", args)
    conf = CONFIG.copy()

    server = ServerPeer(POLLER)
    server.configure(conf)
    server.listen((conf["bittorrent.address"], conf["bittorrent.bt_port"]))

    HTTP_SERVER.configure(conf)
    HTTP_SERVER.listen((conf["bittorrent.address"],
                        conf["bittorrent.http_port"]))

    if conf["bittorrent.daemonize"]:
        system.change_dir()
        system.go_background()
        LOG.redirect()

    system.drop_privileges()
    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
