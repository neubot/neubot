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

import StringIO
import hashlib
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.bittorrent.peer import PeerNeubot
from neubot.compat import json
from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.database import table_bittorrent
from neubot.http.message import Message
from neubot.http.server import ServerHTTP
from neubot.log import LOG
from neubot.net.poller import POLLER
from neubot.notify import NOTIFIER

from neubot import boot
from neubot import system
from neubot import utils

AUTH_PEERS = {}

#
# TODO Here more work is needed to allow authenticated
# clients only and to ensure that there are no memory
# leaks in the shared AUTH_PEERS dictionary.
#
class ServerNegotiator(ServerHTTP):
    def configure(self, conf, measurer=None):
        conf["http.server.rootdir"] = ""
        ServerHTTP.configure(self, conf, measurer)

    def process_request(self, stream, request):
        if request.uri == "/bittorrent/negotiate":
            self.do_negotiate(stream, request)
        elif request.uri == "/bittorrent/collect":
            self.do_collect(stream, request)
        else:
            #TODO be graceful
            raise RuntimeError("Invalid HTTP request")

    #TODO queue management!
    def do_negotiate(self, stream, request):
        uuid = utils.get_uuid()
        m = {
            "authorization": uuid,
            "real_address": stream.peername[0],
            "unchoked": 1,
            "queue_pos": 0,
        }
        sha1 = hashlib.sha1()
        sha1.update(uuid)
        AUTH_PEERS[sha1.digest()] = {}

        s = json.dumps(m)
        stringio = StringIO.StringIO(s)

        response = Message()
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype="application/json")
        stream.send_response(request, response)

    def do_collect(self, stream, request):
        m = json.loads(request.body.read())

        # Retrieve user's results
        sha1 = hashlib.sha1()
        sha1.update(request["authorization"])
        peer_id = sha1.digest()
        result = AUTH_PEERS[peer_id]
        del AUTH_PEERS[peer_id]

        #
        # Merge
        # Note that the following is not a bug: it's just that
        # the server saves results using the point of view of the
        # client, i.e. upload_speed _is_ client's upload speed.
        #
        m["timestamp"] = result["timestamp"]
        m["upload_speed"] = result["upload_speed"]

        if (not utils.intify(m["privacy_informed"]) or
          utils.intify(m["privacy_can_collect"])):
            table_bittorrent.insert(DATABASE.connection(), m)

        s = StringIO.StringIO(json.dumps(m))
        response = Message()
        response.compose(code="200", reason="Ok", body=s,
                         mimetype="application/json")
        stream.send_response(request, response)

class ServerPeer(PeerNeubot):
    def connection_ready(self, stream):
        if not stream.id in AUTH_PEERS:
            raise RuntimeError("Unauthorized peer")
        PeerNeubot.connection_ready(self, stream)

    def complete(self, stream, speed, rtt):
        AUTH_PEERS[stream.id] = {
            #
            # Just a stub: we don't need to save much more then
            # this because the rest is measured by the client.
            # XXX upload because we use the client point of
            # view, so our download speed is its upload speed.
            #
            "timestamp": utils.timestamp(),
            "upload_speed": speed,
        }

CONFIG.register_defaults({
    "bittorrent.address": "0.0.0.0",
    "bittorrent.daemonize": True,
    "bittorrent.http_port": 8000,       #XXX Just for testing
    "bittorrent.bt_port": 9881,
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

    server = ServerNegotiator(POLLER)
    server.configure(conf)
    server.listen((conf["bittorrent.address"], conf["bittorrent.http_port"]))

    server = ServerPeer(POLLER)
    server.configure(conf)
    server.listen((conf["bittorrent.address"], conf["bittorrent.bt_port"]))

    if conf["bittorrent.daemonize"]:
        system.change_dir()
        system.go_background()
        LOG.redirect()

    system.drop_privileges()
    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
