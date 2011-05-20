# neubot/bittorrent/main.py

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

from neubot.config import CONFIG
from neubot.bittorrent.stream import BTStream
from neubot.net.stream import StreamHandler
from neubot.net.measurer import MEASURER
from neubot.net.poller import POLLER
from neubot.arcfour import arcfour_new
from neubot.log import LOG
from neubot import system
from neubot import boot


class Upload(object):

    """Responds to requests."""

    def __init__(self, stream, scramble):
        self.stream = stream
        self.scrambler = None
        if scramble:
            self.scrambler = arcfour_new()
        self.interested = False

    def got_request(self, index, begin, length):
        if not self.interested:
            return
        data = "A" * length
        if self.scrambler:
            data = self.scrambler.encrypt(data)
        self.stream.send_piece(index, begin, data)

    def got_interested(self):
        self.interested = True
        self.stream.send_unchoke()

    def got_not_interested(self):
        self.interested = False
        self.stream.send_choke()

class Download(object):

    """Requests missing pieces."""

    def __init__(self, stream):
        self.stream = stream
        self.choked = True

    def got_piece(self, index, begin, length):
        if self.choked:
            return
        self.stream.send_request(index, 0, 1<<15)

    def got_choke(self):
        self.choked = True

    def got_unchoke(self):
        self.choked = False
        for index in range(0, 32):
            self.stream.send_request(index, 0, 1<<15)

class BTConnectingPeer(StreamHandler):

    """Connect to a given BitTorrent peer and controls the
       resulting connection."""

    def __init__(self, poller):
        StreamHandler.__init__(self, poller)
        self.infohash = "".join( ['\xaa']*20 )
        self.my_id = "".join( ['\xaa']*20 )

    def connection_made(self, sock):
        stream = BTStream(self.poller)
        stream.attach(self, sock, self.conf, self.measurer)
        stream.initialize(self, self.my_id, True)
        stream.download = Download(stream)
        scramble = not self.conf.get("net.stream.obfuscate", False)
        stream.upload = Upload(stream, scramble)

    def connection_handshake_completed(self, stream):
        stream.send_interested()

class BTListeningPeer(StreamHandler):

    """Listens for connections from BitTorrent peers and controls the
       resulting connections."""

    def __init__(self, poller):
        StreamHandler.__init__(self, poller)
        self.infohash = "".join( ['\xaa']*20 )
        self.my_id = "".join( ['\xaa']*20 )

    def connection_made(self, sock):
        stream = BTStream(self.poller)
        stream.attach(self, sock, self.conf, self.measurer)
        stream.initialize(self, self.my_id, True)
        stream.download = Download(stream)
        scramble = not self.conf.get("net.stream.obfuscate", False)
        stream.upload = Upload(stream, scramble)

    def connection_handshake_completed(self, stream):
        pass

def main(args):

    CONFIG.register_defaults({
        "bittorrent.test.address": "",
        "bittorrent.test.daemonize": False,
        "bittorrent.test.duration": 10,
        "bittorrent.test.listen": False,
        "bittorrent.test.port": 6881,
    })
    CONFIG.register_descriptions({
        "bittorrent.test.address": "Set client or server address",
        "bittorrent.test.daemonize": "Enable daemon behavior",
        "bittorrent.test.duration": "Set duration of a test",
        "bittorrent.test.listen": "Enable server mode",
        "bittorrent.test.port": "Set client or server port",
    })

    boot.common("bittorrent.test", "BitTorrent test", args)
    conf = CONFIG.copy()

    if not conf["bittorrent.test.address"]:
        if not conf["bittorrent.test.listen"]:
            conf["bittorrent.test.address"] = "neubot.blupixel.net"
        else:
            conf["bittorrent.test.address"] = "0.0.0.0"

    endpoint = (conf["bittorrent.test.address"],
      conf["bittorrent.test.port"])

    if not (conf["bittorrent.test.listen"] and
            conf["bittorrent.test.daemonize"]):
        MEASURER.start()

    if conf["bittorrent.test.listen"]:
        if conf["bittorrent.test.daemonize"]:
            system.change_dir()
            system.go_background()
            LOG.redirect()
        system.drop_privileges()
        listener = BTListeningPeer(POLLER)
        listener.configure(conf, MEASURER)
        listener.listen(endpoint)
        POLLER.loop()
        sys.exit(0)

    duration = conf["bittorrent.test.duration"]
    if duration >= 0:
        duration = duration + 0.1       # XXX
        POLLER.sched(duration, POLLER.break_loop)

    connector = BTConnectingPeer(POLLER)
    connector.configure(conf, MEASURER)
    connector.connect(endpoint)
    POLLER.loop()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
