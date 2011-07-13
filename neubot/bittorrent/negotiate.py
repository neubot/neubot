# neubot/bittorrent/negotiate.py

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

#
# Negotiate server of the BitTorrent test
# This is built on top of the generic facilities
# provided by neubot/negotiate.py (which may
# become neubot/negotiate/server.py at any point
# in the future)
#

import hashlib

from neubot.compat import json
from neubot.database import table_bittorrent
from neubot.database import DATABASE
from neubot.log import LOG
from neubot.negotiate import NegotiatorModule
from neubot.negotiate import NegotiatorEOF
from neubot.negotiate import NEGOTIATOR

from neubot import privacy

def _make_btid(sid):
    return hashlib.sha1(sid).digest()

#
# This table is shared with the code that
# manages BitTorrent test server.
#
AUTH_PEERS = {}

class _Module(NegotiatorModule):
    def __init__(self):
        self._streams = {}

    def unchoke(self, m):
        btid = _make_btid(m["ident"])
        if btid not in AUTH_PEERS:
            self._streams[m["stream"]] = btid
            m["stream"].atclose(self._at_close)
            target_bytes = int(m["request_body"]["target_bytes"])
            if target_bytes < 0:
                raise RuntimeError("Invalid target_bytes")
            AUTH_PEERS[btid] = {"target_bytes": target_bytes}
        else:
            LOG.oops("Multiple negotiation requests")

    def collect(self, m):
        btid = _make_btid(m["ident"])

        if btid not in AUTH_PEERS:
            raise NegotiatorEOF()

        d = m["request_body"]
        result = AUTH_PEERS[btid]

        #
        # Note that the following is not a bug: it's just that
        # the server saves results using the point of view of the
        # client, i.e. upload_speed _is_ client's upload speed.
        #
        d["timestamp"] = result["timestamp"]
        d["upload_speed"] = result["upload_speed"]

        if privacy.collect_allowed(d):
            table_bittorrent.insert(DATABASE.connection(), d)

        #
        # After we've saved the result into the dictionary we
        # can add extra information we would like to return to
        # the client.
        #
        d["target_bytes"] = result["target_bytes"]

        m["response_body"] = d

    def _at_close(self, stream, exception):
        #
        # XXX Since AUTH_PEERS is cheched by bittorrent
        # code only on connection made, this means we
        # rely uniquely on the watchdog mechanism to stop
        # the bittorrent side of a misbehaving peer.
        #
        btid = self._streams[stream]
        del self._streams[stream]
        del AUTH_PEERS[btid]

NEGOTIATOR.register("bittorrent", _Module())
