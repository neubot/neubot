# neubot/bittorrent/client.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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
from neubot.config import CONFIG
from neubot.compat import json
from neubot.database import DATABASE
from neubot.database import table_bittorrent
from neubot.http.client import ClientHTTP
from neubot.http.message import Message
from neubot.log import LOG
from neubot.net.poller import POLLER
from neubot.notify import NOTIFIER
from neubot.state import STATE

from neubot import boot
from neubot import privacy
from neubot import utils

TESTDONE = "testdone"

class BitTorrentClient(ClientHTTP):
    def __init__(self, poller):
        ClientHTTP.__init__(self, poller)
        self.negotiating = True
        self.http_stream = None
        self.success = False
        self.my_side = {}

    def connect_uri(self, uri=None, count=None):
        if not uri:
            uri = self.conf.get("bittorrent.uri",
              "http://neubot.blupixel.net/")
        ClientHTTP.connect_uri(self, uri, 1)

    def connection_ready(self, stream):
        request = Message()
        request.compose(method="GET", pathquery="/bittorrent/negotiate",
          host=self.host_header)
        request["authorization"] = self.conf.get("_authorization", "")
        stream.send_request(request)

    def got_response(self, stream, request, response):
        if self.negotiating:
            self.got_response_negotiating(stream, request, response)
        else:
            self.got_response_collecting(stream, request, response)

    def got_response_negotiating(self, stream, request, response):
        m = json.loads(response.body.read())

        PROPERTIES = ("authorization", "real_address", "unchoked")
        for k in PROPERTIES:
            self.conf["_%s" % k] = m[k]
        if "queue_pos" in m:
            self.conf["_queue_pos"] = m["queue_pos"]

        if not self.conf["_unchoked"]:
            self.connection_ready(stream)
        else:
            sha1 = hashlib.sha1()
            sha1.update(m["authorization"])
            self.conf["bittorrent.my_id"] = sha1.digest()
            self.http_stream = stream
            self.negotiating = False
            peer = PeerNeubot(self.poller)
            peer.complete = self.peer_test_complete
            peer.connection_lost = self.peer_connection_lost
            peer.configure(self.conf)
            peer.connect((self.http_stream.peername[0], 9881))      #XXX

    def peer_connection_lost(self, stream):
        if not self.success:
            stream = self.http_stream

            #
            # FIXME The following code is wrong because it will
            # nonetheless be parsed as a valid JSON.  Let's leave
            # it like this for this initial testing phase but it
            # definitely needs to be fixed before 0.4 release.
            #
            s = json.dumps({})
            stringio = StringIO.StringIO(s)

            request = Message()
            request.compose(method="POST", pathquery="/bittorrent/collect",
              body=stringio, mimetype="application/json", host=self.host_header)
            request["authorization"] = self.conf.get("_authorization", "")

            stream.send_request(request)

    def peer_test_complete(self, stream, download_speed, rtt):
        self.success = True
        stream = self.http_stream

        self.my_side = {
            # The server will override our timestamp
            "timestamp": utils.timestamp(),
            "uuid": self.conf.get("uuid"),
            "internal_address": stream.myname[0],
            "real_address": self.conf.get("_real_address", ""),
            "remote_address": stream.peername[0],

            "privacy_informed": self.conf.get("privacy.informed", 0),
            "privacy_can_collect": self.conf.get("privacy.can_collect", 0),
            "privacy_can_share": self.conf.get("privacy.can_share", 0),

            # Upload speed measured at the server
            "connect_time": rtt,
            "download_speed": download_speed,
        }

        s = json.dumps(self.my_side)
        stringio = StringIO.StringIO(s)

        request = Message()
        request.compose(method="POST", pathquery="/bittorrent/collect",
          body=stringio, mimetype="application/json", host=self.host_header)
        request["authorization"] = self.conf.get("_authorization", "")

        stream.send_request(request)

    def got_response_collecting(self, stream, request, response):
        if self.success:
            m = json.loads(response.body.read())
            #
            # Always measure at the receiver because there is more
            # information at the receiver and also to make my friend
            # Enrico happier :-P.
            # The following is not a bug: it's just that the server
            # returns a result using the point of view of the client,
            # i.e. upload_speed is _our_ upload speed.
            #
            self.my_side["upload_speed"] = m["upload_speed"]
            if privacy.collect_allowed(self.my_side):
                table_bittorrent.insert(DATABASE.connection(), self.my_side)

        stream.close()

    def connection_lost(self, stream):
        NOTIFIER.publish(TESTDONE)

CONFIG.register_defaults({
    "bittorrent.uri": "http://neubot.blupixel.net/",
})

def main(args):
    CONFIG.register_descriptions({
        "bittorrent.uri": "Base URI to connect to",
    })

    boot.common("bittorrent.negotiate_client",
      "BitTorrent negotiate client", args)
    conf = CONFIG.copy()
    client = BitTorrentClient(POLLER)
    client.configure(conf)
    client.connect_uri()
    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
