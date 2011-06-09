# neubot/bittorrent/__init__.py

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

from neubot.bittorrent.peer import PIECE_LEN
from neubot.bittorrent.peer import Peer
from neubot.config import CONFIG
from neubot.log import LOG
from neubot.net.measurer import MEASURER
from neubot.net.poller import POLLER

from neubot import boot
from neubot import system

class ConnectingPeer(Peer):
    def complete(self, speed, rtt):
        POLLER.sched(1, POLLER.break_loop)

def main(args):

    CONFIG.register_defaults({
        "bittorrent.address": "",
        "bittorrent.daemonize": False,
        "bittorrent.dload_speed": 0,
        "bittorrent.listen": False,
        "bittorrent.piece_len": PIECE_LEN,
        "bittorrent.port": 6881,
    })
    CONFIG.register_descriptions({
        "bittorrent.address": "Set client or server address",
        "bittorrent.daemonize": "Enable daemon behavior",
        "bittorrent.dload_speed": "Estimate dload speed [Mbit/s] (0 = guess)",
        "bittorrent.listen": "Enable server mode",
        "bittorrent.piece_len": "Length of a single piece",
        "bittorrent.port": "Set client or server port",
    })

    boot.common("bittorrent", "BitTorrent test", args)
    conf = CONFIG.copy()

    if not conf["bittorrent.address"]:
        if not conf["bittorrent.listen"]:
            conf["bittorrent.address"] = "neubot.blupixel.net"
        else:
            conf["bittorrent.address"] = "0.0.0.0"

    endpoint = (conf["bittorrent.address"],
      conf["bittorrent.port"])

    if conf["bittorrent.dload_speed"]:
        dload_speed = int(conf["bittorrent.dload_speed"])

        # Mbit/s -> bytes/s
        dload_speed *= 1000 * 1000
        dload_speed >>= 3

        # We want about 5 seconds of test
        conf["bittorrent.target_bytes"] = 5 * dload_speed

    if conf["bittorrent.listen"]:
        if conf["bittorrent.daemonize"]:
            system.change_dir()
            system.go_background()
            LOG.redirect()
        system.drop_privileges()
        listener = Peer(POLLER)
        listener.configure(conf, MEASURER)
        listener.listen(endpoint)
        POLLER.loop()
        sys.exit(0)

    connector = ConnectingPeer(POLLER)
    connector.configure(conf, MEASURER)
    connector.connect(endpoint)
    POLLER.loop()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
